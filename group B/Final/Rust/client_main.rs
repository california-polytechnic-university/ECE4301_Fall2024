use std::io;
use std::io::{Write, Read};
use std::fs;
use std::net::TcpStream;
use std::collections::VecDeque;
use std::time::{Duration, Instant};

use rand::Rng;

use crossbeam::channel::{select, unbounded};
use crossbeam_utils::thread;

use rsa::{Pkcs1v15Encrypt, RsaPublicKey};
use rsa::pkcs8::DecodePublicKey;

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

    //Threads & network setup
    let (s1, r1) = unbounded::<String>();
    let (s2, r2) = unbounded::<Vec<u8>>();
    let (s3, r3) = unbounded::<Vec<u8>>();
    let mut stream = TcpStream::connect("localhost:7878").unwrap();

    //Get username
    let mut username = String::new();
    println!("Please enter your username: ");
    std::io::stdin().read_line(&mut username).expect("Failed to read line");

    //Gets ChaCha20 key from user
    let mut my_key = get_key();
    let mut enc_key: Vec<u8> = Vec::new();

    //Spawn the threads
    thread::scope(|s| {
        //Thread to send messages
        s.spawn(move |_| {
            let type_buffer: Vec<u8> = vec![0; 1];
            stream.write(&type_buffer).unwrap();

            //Sends username & its length to server
            stream.write(&usize::to_ne_bytes(username.trim().len())).unwrap();
            stream.write(&username.trim().as_bytes()).unwrap();

            let ke_start = Instant::now();
            //Gets rsa key from server
            let mut rsakey_buffer = [0; 451];
            stream.read(&mut rsakey_buffer).unwrap();

            //Saves rsa key as pem file
            let mut file_name = String::from("key.pem");
            let mut file = fs::OpenOptions::new().create(true).write(true).open(file_name.clone()).unwrap();
            file.write_all(&rsakey_buffer).expect("Couldn't write to file");

            //Makes RsaPublicKey from pem file
            let pub_key = RsaPublicKey::from_public_key_pem(&fs::read_to_string(file_name).unwrap()).unwrap();
            let ke_duration = ke_start.elapsed();
            println!("RSA key received from server in {:?}", ke_duration);

            //Encrypts ChaCha20 key using rsa
            let mut rng = rand::thread_rng();
            let key_enc_start = Instant::now();
            enc_key = pub_key.encrypt(&mut rng, Pkcs1v15Encrypt, &convert_key(my_key)).expect("failed to encrypt");
            let key_enc_duration = key_enc_start.elapsed();
            println!("ChaCha20 key encrypted using RSA in {:?}", ke_duration);

            //Sends encrypted ChaCha20 key to server
            stream.write(&enc_key[..]);
            s3.send(enc_key).unwrap();

            //Whenever the threads receives user input from other thread
            loop {
                select! {
                    recv(r1) -> msg => {
                        let mut message = &msg.unwrap();
                        //Appends username to start of message
                        let mut message = username.trim().to_owned() + ": " + message;

                        let message_enc_start = Instant::now();
                        //Sets up ChaCha20 for encryption
                        let mut encryption_buffer = Buffer {
                            queue: VecDeque::with_capacity(message.len() as usize),
                        };

                        for i in 0..encryption_buffer.queue.capacity() {
                            encryption_buffer.queue.push_back(message.as_bytes()[i]);
                        }

                        //Encrypts message using ChaCha20
                        let my_encrypted_data: Vec<u8> = encryption_buffer.cipher(my_key, 1, false);
                        let message_enc_duration = message_enc_start.elapsed();
                        println!("Message encrypted using ChaCha20 in {:?}", message_enc_duration);

                        //Sends length of message & its encrypted content to server
                        let ready: Vec<u8> = vec![1; 1];
                        stream.write(&ready).unwrap();
                        stream.write(&usize::to_ne_bytes(my_encrypted_data.len())).unwrap();
                        stream.write(&my_encrypted_data).unwrap();
                    },
                    //Whenever a message is received from the server
                    recv(r2) -> msg => {
                        //Prints message
                        println!("{}", String::from_utf8_lossy(&msg.unwrap()[..]).trim_matches(char::from(0)));
                    },
                }
            }

        });

        //Thread to get user input
        s.spawn(move |_| {
           loop {
                let mut message = String::new();
                std::io::stdin()
                .read_line(&mut message)
                .expect("Failed to read line");

                match message.as_str().trim() {
                    "!quit" => break,
                    _ => s1.send(message.trim().to_string()).unwrap(),
                };
            }
        });

        //Thread to receive messages
        s.spawn(move |_| {
            let mut stream = TcpStream::connect("localhost:7879").unwrap();
            let type_buffer: Vec<u8> = vec![1; 1];
            stream.write(&type_buffer).unwrap();

            //Gets encrypted ChaCha20 key from other thread & sends it to server's second thread
            let enc_key = r3.recv().unwrap();
            stream.write(&enc_key[..]);

            let mut message_buffer = vec!(0; 256);
            loop {

                //Gets the size of the message being received
                let mut message_size_buffer: Vec<u8> = vec![0; 8];
                stream.read(&mut message_size_buffer).unwrap();
                let message_size: [u8; 8] = message_size_buffer.try_into().unwrap();

                //Gets message from server
                message_buffer = vec![0; usize::from_ne_bytes(message_size)];
                stream.read(&mut message_buffer).unwrap();

                let message_dec_start = Instant::now();
                //Sets up ChaCha20 cipher for decryption
                let mut decryption_buffer = Buffer {
                    queue: VecDeque::with_capacity(usize::from_ne_bytes(message_size)),
                };

                for i in 0..decryption_buffer.queue.capacity() {
                   decryption_buffer.queue.push_back(message_buffer[i]);
                }

                //Sends decrypted message to other thread to be displayed
                let my_decrypted_data = decryption_buffer.cipher(my_key, 1, true);
                let message_dec_duration = message_dec_start.elapsed();
                println!("Message decrypted using ChaCha20 in {:?}", message_dec_duration);

                s2.send(my_decrypted_data).unwrap();
                message_buffer = vec!(0; 256);
             }
         });

    }).unwrap();

}

fn get_key() -> [u32; 8] {
    //Prompts user to input key
    let key_str = loop {
        println!("Enter the key:");

        let mut buffer = String::new();
        io::stdin()
            .read_line(&mut buffer)
            .expect("Failed to read line");

        buffer = buffer.trim().to_string();

        if buffer.len() == 64 { break buffer; } else { println!("Key should be 64 characters long."); }
    };

    //Splits user input string into groups of 8 characters (8 hex -> 32 bits)
    let mut key_parts_str = Vec::new();
    key_parts_str.push(key_str);

    for i in 1..8 {
        let last_part = key_parts_str[i-1].split_off(8);
        key_parts_str.push(last_part);
    }

    //Converts groups' hex values to u32, converts to bytes, then converts bytes to u32
    let mut key_parts: [u32; 8] = [0; 8];
    for j in 0..8 {
        key_parts[j] = u32::from_be_bytes(u32::from_str_radix(key_parts_str[j].trim(), 16).unwrap().to_le_bytes());
    }

    key_parts
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

fn convert_key(arr: [u32; 8]) -> [u8; 32] {
    //Converts 8 u32s into 32 u8s
    let mut res = [0; 32];
    for i in 0..32 {
        res[i] = arr[i/4].to_le_bytes()[i%4];
    }

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

fn save_data(data: &Vec<u8>, name: &String) {
    //Creates a file and saves the data's bytes to it
    let mut file = fs::OpenOptions::new().create(true).write(true).open(&name).unwrap();
    file.write_all(&data).expect("Couldn't write to file");
}