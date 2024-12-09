use std::io::{Write, Read};
use std::fs::File;
use std::net::{TcpListener, TcpStream};
use std::collections::VecDeque;
use std::time::{Duration, Instant};

use rand::Rng;

use crossbeam::channel::{select, unbounded};
use crossbeam_utils::thread;

use sec1::LineEnding::LF;
use rsa::{Pkcs1v15Encrypt, RsaPrivateKey, RsaPublicKey};
use rsa::pkcs8::EncodePublicKey;

//Constant used in Chacha20
const CONSTANT: [u32; 4] = [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574];

//Chacha20 state
struct State {
    array: [u32; 16],
}

//Buffer containing data to be encrypted/decrypted
struct Buffer {
    queue: VecDeque<u8>,
}

fn main() {

    //Sets up threads
    let (s1, r1) = unbounded::<Vec<u8>>();
    let (s2, r2) = (s1.clone(), r1.clone());
    let (s3, r3) = unbounded::<RsaPrivateKey>();
    let (s4, r4) = (s3.clone(), r3.clone());

    thread::scope(|s| {
        s.spawn(move |_| {

            //Starts listening on port 7878
            let listener = TcpListener::bind("0.0.0.0:7878").unwrap();

            //Runs handle_client on each stream
            for stream in listener.incoming() {
                handle_client(stream.unwrap(), &s1, &r1, &s3, &r3);
            }

        });

        s.spawn(move |_| {

            //Starts listening on port 7879
            let listener = TcpListener::bind("0.0.0.0:7879").unwrap();

            //Runs handle_client on each stream
            for stream in listener.incoming() {
                handle_client(stream.unwrap(), &s2, &r2, &s4, &r4);
            }

         });

    }).unwrap();
}

fn handle_client(mut stream: TcpStream, s1: &crossbeam::channel::Sender<Vec<u8>>, r1: &crossbeam::channel::Receiver<Vec<u8>>, s2: &crossbeam::channel::Sender<RsaPrivateKey>, r2: &crossbeam::channel::Receiver<RsaPrivateKey>) {
    let mut type_buffer: Vec<u8> = vec![0; 1];
    stream.read(&mut type_buffer).unwrap();

    if type_buffer[0] == 0 {

        //Gets username & its length from client
        let mut name_size_buffer: Vec<u8> = vec![0; 8];
        stream.read(&mut name_size_buffer).unwrap();
        let name_size: [u8; 8] = name_size_buffer.try_into().unwrap();

        let mut username_buffer: Vec<u8> = vec![0; usize::from_ne_bytes(name_size)];
        stream.read(&mut username_buffer).unwrap();

        let ke_start = Instant::now();
        //Set up RSA by generating key pair
        let mut rng = rand::thread_rng();
        let bits = 2048;
        let priv_key = RsaPrivateKey::new(&mut rng, bits).expect("failed to generate a key");
        let pub_key = RsaPublicKey::from(&priv_key);
        s2.send(priv_key.clone()).unwrap();

        //Gets public key into vector to send
        let mut file_name = String::from_utf8_lossy(&username_buffer).trim_matches(char::from(0)).to_owned() + "_receive_key.pem";
        pub_key.write_public_key_pem_file(file_name.clone(), LF);
        let mut f = File::open(file_name.clone()).unwrap();
        let mut pubkey_buffer = vec![0; f.metadata().unwrap().len() as usize];
        f.read(&mut pubkey_buffer[..]).unwrap();

        //Sends the public key
        stream.write(&pubkey_buffer[..]).unwrap();
        let ke_duration = ke_start.elapsed();
        println!("RSA key generated & sent to client in {:?}", ke_duration);

        //Gets encrypted ChaCha20 key from client
        let mut key_buffer = vec![0; 256];
        stream.read(&mut key_buffer).unwrap();

        //Decrypts ChaCha20 key using rsa key
        let key_dec_start = Instant::now();
        key_buffer = priv_key.decrypt(Pkcs1v15Encrypt, &key_buffer).expect("failed to decrypt");
        let key_dec_duration = key_dec_start.elapsed();
        println!("ChaCha20 key decrypted in {:?}", key_dec_duration);

        //Receives messages from the client
        let mut ready_buffer = vec![0; 1];
        stream.read(&mut ready_buffer).unwrap();

        let mut message_buffer = vec![0; 256];
        let mut my_decrypted_data = vec![0; 256];
        loop {
            if ready_buffer[0] == 1 {
                //Gets the size of the message being received
                let mut message_size_buffer: Vec<u8> = vec![0; 8];
                stream.read(&mut message_size_buffer).unwrap();
                let message_size: [u8; 8] = message_size_buffer.try_into().unwrap();

                //Receives encrypted message from client
                message_buffer = vec![0; usize::from_ne_bytes(message_size)];
                stream.read(&mut message_buffer).unwrap();
                let mut message = String::new();

                let message_dec_start = Instant::now();
                //Sets up ChaCha20 for decryption
                let mut decryption_buffer = Buffer {
                    queue: VecDeque::with_capacity(usize::from_ne_bytes(message_size)),
                };

                for i in 0..decryption_buffer.queue.capacity() {
                    decryption_buffer.queue.push_back(message_buffer[i]);
                }

                //Decrypts message & sends to other thread to send to clients
                my_decrypted_data = decryption_buffer.cipher(convert_key(&key_buffer[..]), 1, true);
                let message_dec_duration = message_dec_start.elapsed();
                println!("Message decrypted using ChaCha20 in {:?}", message_dec_duration);

                message = String::from_utf8_lossy(&my_decrypted_data).to_string();
                s1.send(my_decrypted_data.clone()).unwrap();

                message_buffer = vec![0; 256];
                ready_buffer[0] = 0;
            }

            stream.read(&mut ready_buffer).unwrap();
        }

    } else if type_buffer[0] == 1 {

        //Gets private rsa key from other thread
        let priv_key = r2.recv().unwrap();

        //Receives client's encrypted ChaCha20 key and decrypts it using rsa key
        let mut key_buffer = vec![0; 256];
        stream.read(&mut key_buffer).unwrap();
        key_buffer = priv_key.decrypt(Pkcs1v15Encrypt, &key_buffer).expect("failed to decrypt");

        loop {
        select! {
                recv(r1) -> msg => {

                    //Encrypts messages received from other thread using client's decrypted ChaCha20 key before sending
                    let message = msg.unwrap();

                    let message_enc_start = Instant::now();
                    let mut encryption_buffer = Buffer {
                        queue: VecDeque::with_capacity(message.len() as usize),
                    };

                    for i in 0..encryption_buffer.queue.capacity() {
                        encryption_buffer.queue.push_back(message[i]);
                    }

                    let my_encrypted_data: Vec<u8> = encryption_buffer.cipher(convert_key(&key_buffer[..]), 1, false);
                    let message_enc_duration = message_enc_start.elapsed();
                    println!("Message encrypted using ChaCha20 in {:?}", message_enc_duration);

                    //Sends encrypted messages to clients
                    stream.write(&usize::to_ne_bytes(my_encrypted_data.len())).unwrap();
                    stream.write(&my_encrypted_data[..]);
                }
            }
        }
     }
}

fn chacha_block(key: [u32; 8], counter: u32, nonce: [u32; 3]) -> State {
    //Initializes state and runs the block encryption
    let mut my_state = init_state(key, counter, nonce);
    my_state.block();

    my_state
}

impl State {
    fn block(&mut self) {
        //Creates working state, runs rounds on it, adds with initial array
        let mut working_state = State {
            array: self.array,
        };

        working_state.rounds();

        for i in 0..16 {
            self.array[i] = self.array[i].wrapping_add(working_state.array[i]);
        }
    }

    //Chacha complete rounds
    fn rounds(&mut self) {
        for _ in 0..10 {
            self.quarter_round(0, 4, 8, 12);
            self.quarter_round(1, 5, 9, 13);
            self.quarter_round(2, 6, 10, 14);
            self.quarter_round(3, 7, 11, 15);

            self.quarter_round(0, 5, 10, 15);
            self.quarter_round(1, 6, 11, 12);
            self.quarter_round(2, 7, 8, 13);
            self.quarter_round(3, 4, 9, 14);
        }
    }

    //Chacha quarter round
    fn quarter_round(&mut self, a: usize, b: usize, c: usize, d: usize) {
        self.array[a] = self.array[a].wrapping_add(self.array[b]); self.array[d] ^= self.array[a]; self.array[d] = self.array[d].rotate_left(16);
        self.array[c] = self.array[c].wrapping_add(self.array[d]); self.array[b] ^= self.array[c]; self.array[b] = self.array[b].rotate_left(12);
        self.array[a] = self.array[a].wrapping_add(self.array[b]); self.array[d] ^= self.array[a]; self.array[d] = self.array[d].rotate_left(8);
        self.array[c] = self.array[c].wrapping_add(self.array[d]); self.array[b] ^= self.array[c]; self.array[b] = self.array[b].rotate_left(7);
    }
}

fn init_state(key: [u32; 8], counter: u32, nonce: [u32; 3]) -> State {
    //Initializes state
    let constructed_array: [u32; 16] = [CONSTANT[0], CONSTANT[1], CONSTANT[2], CONSTANT[3],
                            key[0], key[1], key[2], key[3],
                            key[4], key[5], key[6], key[7],
                            counter, nonce[0], nonce[1], nonce[2]];

    State {
        array: constructed_array,
    }
}

fn convert(arr: [u32; 16]) -> [u8; 64] {
    //Converts 16 u32s into 64 u8s
    let mut res = [0; 64];
    for i in 0..64 {
        res[i] = arr[i/4].to_le_bytes()[i%4];
    }

    res
}

fn convert_key(arr: &[u8]) -> [u32; 8] {
    let mut res = [0; 8];
    res[0] = u32::from_le_bytes([arr[0], arr[1], arr[2], arr[3]]);
    res[1] = u32::from_le_bytes([arr[4], arr[5], arr[6], arr[7]]);
    res[2] = u32::from_le_bytes([arr[8], arr[9], arr[10], arr[11]]);
    res[3] = u32::from_le_bytes([arr[12], arr[13], arr[14], arr[15]]);
    res[4] = u32::from_le_bytes([arr[16], arr[17], arr[18], arr[19]]);
    res[5] = u32::from_le_bytes([arr[20], arr[21], arr[22], arr[23]]);
    res[6] = u32::from_le_bytes([arr[24], arr[25], arr[26], arr[27]]);
    res[7] = u32::from_le_bytes([arr[28], arr[29], arr[30], arr[31]]);

    res
}

impl Buffer {
    //Main cipher function
    fn cipher(&mut self, key: [u32; 8], mut counter: u32, decrypt: bool) -> Vec<u8> {
        //Creates vector for final data, a vector for the nonces used, and sets up rng for encryption
        let mut final_data = Vec::new();
        let mut nonces = VecDeque::new();
        let mut rng = rand::thread_rng();

        //In the case of decryption, the random nonces used need to be retreived
        if decrypt {
            //Gets the number of blocks used, thus the portion of the data that is the nonces
            let blocks = u32::from_le_bytes([self.queue.pop_back().unwrap(), self.queue.pop_back().unwrap(), self.queue.pop_back().unwrap(), self.queue.pop_back().unwrap()]);

            //Gets the bytes of each u32 of the nonces, converts to u32s, push to nonces vector to use
            for _ in 0..blocks {
                let mut nonce: [u32; 3] = [0; 3];
                for i in 0..3 {
                    nonce[2-i] = u32::from_le_bytes([self.queue.pop_back().unwrap(), self.queue.pop_back().unwrap(), self.queue.pop_back().unwrap(), self.queue.pop_back().unwrap()]);
                }
                nonces.push_back(nonce);
            }
        }

        //While there is still data in the buffer
        while !self.queue.is_empty() {
            let mut nonce: [u32; 3] = [0; 3];

            //If encryption, generate random nonce for block, else retrieve from earlier
            if !decrypt {
                nonce = [rng.gen::<u32>(), rng.gen::<u32>(), rng.gen::<u32>()];
                nonces.push_back(nonce);
            } else {
                nonce = nonces.pop_front().unwrap();
            }

            //Generate the keystream
            let key_stream: [u8; 64] = convert(chacha_block(key, counter, nonce).array);

            //Maximum 64 bytes of data per block
            if self.queue.len() >= 64 {
                for i in 0..64 {
                    final_data.push(self.queue.pop_front().unwrap() ^ key_stream[i]);
                }
            } else {
                for i in 0..self.queue.len() {
                    final_data.push(self.queue.pop_front().unwrap() ^ key_stream[i]);
                }
            }

            //Increment counter for next block's state
            counter += 1;
        }

        //In case of encryption, saves the bytes of nonces used to final data
        if !decrypt {
            let blocks = counter-1;

            for _ in 0..blocks {
                let nonce_arr = nonces.pop_back().unwrap();
                for i in 0..3 {
                    let nonce = nonce_arr[i];
                    for j in 0..4 {
                        let nonce_byte = nonce.to_be_bytes()[j];
                        final_data.push(nonce_byte);
                    }
                }
            }

           //Saves number of blocks processed to let decryption know how much of data is nonces
           for l in 0..4 {
               final_data.push(blocks.to_be_bytes()[l]);
           }
        }

        final_data
    }
}