use std::io;
use std::io::{stdin, stdout, Write, Read};
use std::fs;
use std::fs::File;
use std::collections::VecDeque;
use std::process::Command;
use std::time::{Duration, Instant};
use rand::Rng;
use termion::event::Key;
use termion::input::TermRead;
use termion::raw::IntoRawMode;
use clap::{arg, command, ArgAction, Command as ClapCommand};

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
    //Check which mode is ran
    let matches = command!()
        .subcommand(
            ClapCommand::new("encrypt")
                .about("Encrypts data")
                .arg(arg!(-f --file "Encrypts specified file").action(ArgAction::SetTrue))
                .arg(arg!(-d --delete "Deletes file after encryption").action(ArgAction::SetTrue)),
        )
 .subcommand(
            ClapCommand::new("decrypt")
                .about("Decrypts data")
                .arg(arg!(-f --file "Decrypts specified file").action(ArgAction::SetTrue)),
        )
        .get_matches();

    //If Encrypt subcommand is ran
    if let Some(matches) = matches.subcommand_matches("encrypt") {

        //If -f is ran, get desired path. Else default to camera
        let mut file_name = String::new();
        if matches.get_flag("file") {

            println!("Enter the path to the file:");
            io::stdin()
                .read_line(&mut file_name)
                .expect("Failed to read line");
            file_name = String::from(file_name.trim());

        } else {
            //Saves video from camera
            get_video();
            file_name = String::from("output.mkv");
        }

        //Opens the video file, creates a Buffer, saves bytes to buffer
        let mut f = File::open(&file_name).unwrap();
        let mut buffer = vec![0; f.metadata().unwrap().len() as usize];
        f.read(&mut buffer[..]).unwrap();

        //Gets key from user, sets counter to 1
        let my_key: [u32; 8] = get_key();
        let my_counter: u32 = 1;

        let mut encryption_buffer = Buffer {
            queue: VecDeque::with_capacity(f.metadata().unwrap().len() as usize),
        };

        for i in 0..encryption_buffer.queue.capacity() {
            encryption_buffer.queue.push_back(buffer[i]);
        }

        //Runs encryption on the buffer, saves bytes to file
        let start = Instant::now();
        let my_encrypted_data: Vec<u8> = encryption_buffer.cipher(my_key, my_counter, false);
        let duration = start.elapsed();
        let encrypted_name = String::from("encrypted");
        save_data(&my_encrypted_data, &encrypted_name);
        println!("Encrypted data in {:?} and saved as 'encrypted'.", duration);

        //Deletes plaintext after encryption if -d is used
        if matches.get_flag("delete") {
            fs::remove_file(&file_name).unwrap();
        }
    }

    //If Decrypt subcommand is ran
    if let Some(matches) = matches.subcommand_matches("decrypt") {

        //If -f is ran, get desired path. Else use default encrypted file
        let mut file_name = String::new();
        if matches.get_flag("file") {

            println!("Enter the path to the file:");
            io::stdin()
                .read_line(&mut file_name)
                .expect("Failed to read line");
            file_name = String::from(file_name.trim());

        } else {
            file_name = String::from("encrypted");
        }

        //Gets key from user, sets counter to 1
        let my_key: [u32; 8] = get_key();
        let my_counter: u32 = 1;

        //Opens the encrypted file, creates a Buffer, saves bytes to buffer
        let mut f = File::open(&file_name).unwrap();
        let mut buffer = vec![0; f.metadata().unwrap().len() as usize];
        f.read(&mut buffer[..]).unwrap();

        let mut decryption_buffer = Buffer {
            queue: VecDeque::with_capacity(f.metadata().unwrap().len() as usize),
        };

        for i in 0..decryption_buffer.queue.capacity() {
            decryption_buffer.queue.push_back(buffer[i]);
        }

        //Runs decryption on the buffer, saves bytes to file
        let start = Instant::now();
        let my_decrypted_data: Vec<u8> = decryption_buffer.cipher(my_key, my_counter, true);
        let duration = start.elapsed();

        //Request desired output file name
        let mut output_name = String::new();
        println!("Enter name for output file:");
        io::stdin()
            .read_line(&mut output_name)
            .expect("Failed to read line");
        output_name = String::from(output_name.trim());

        //Saves data to file with specified name
        save_data(&my_decrypted_data, &output_name);
        println!("Decrypted data in {:?} and saved as '{}'.", duration, output_name);
    }
}

fn get_video() {
    //Spawns child ffmpeg process to save camera video
    let mut child = Command::new("ffmpeg")
        .args(["-hide_banner", "-y", "-f", "v4l2", "-input_format", "h264", "-framerate", "24", "-video_size", "1920x1080", "-i", "/dev/video0", "output.mkv"])
        .spawn()
        .unwrap();

    //Clear screen
    let stdin = stdin();
    let mut stdout = stdout().into_raw_mode().unwrap();

    //Waits until user presses 'q'
    for c in stdin.keys() {
        match c.unwrap() {
            Key::Char('q') => break,
            _ => (),
        }
        stdout.flush().unwrap();
    }

    //After user presses 'q' send SIGINT to child process
    nix::sys::signal::kill(
        nix::unistd::Pid::from_raw(child.id() as i32),
        nix::sys::signal::Signal::SIGINT
    ).expect("cannot send ctrl-c");

    //Clears terminal
    write!(
        stdout,
        "{}{}",
        termion::cursor::Goto(1, 1),
        termion::clear::All
    )
    .unwrap();

    //Waits for child process to be killed
    child.wait().unwrap();
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
