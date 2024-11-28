use std::io::{stdin, stdout, Write, Read};
use std::fs;
use std::process::Command;
use std::net::{TcpListener, TcpStream};
use std::time::{Duration, Instant};

use rsa::{Pkcs1v15Encrypt, RsaPublicKey};
use rsa::pkcs8::DecodePublicKey;
use aes_gcm::{
    aead::{Aead, AeadCore, KeyInit, OsRng},
    Aes256Gcm
};

use termion::event::Key as TermKey;
use termion::input::TermRead;
use termion::raw::IntoRawMode;

fn main() {

    //Starts listening on port 8080
    let listener = TcpListener::bind("0.0.0.0:7878").unwrap();

    //Runs handle_client on each stream
    for stream in listener.incoming() {
        handle_client(stream.unwrap());
    }

}

fn handle_client(mut stream: TcpStream) {

    //Receive the public RSA key
    let ke_start = Instant::now();
    let mut rsakey_buffer = [0; 451];
    stream.read(&mut rsakey_buffer).unwrap();

    //Save key as pem file (Better solution probably exists)
    let mut file = fs::OpenOptions::new().create(true).write(true).open("key.pem").unwrap();
    file.write_all(&rsakey_buffer).expect("Couldn't write to file");
    println!("RSA key received and saved as key.pem");

    //Makes RsaPublicKey from pem file
    let public_key = RsaPublicKey::from_public_key_pem(&fs::read_to_string("key.pem").unwrap()).unwrap();

    //Generate the AES key
    let aeskey = Aes256Gcm::generate_key(OsRng);
    let nonce = Aes256Gcm::generate_nonce(&mut OsRng); // 96-bits; unique per message

    //Encrypt the AES key using RSA
    let mut rng = rand::thread_rng();
    let enc_data = public_key.encrypt(&mut rng, Pkcs1v15Encrypt, &aeskey[..]).expect("failed to encrypt");

    //Sends the AES key and the nonce used
    stream.write(&enc_data).unwrap();
    let ke_duration = ke_start.elapsed();
    println!("AES key sent: {:x}, {:?} since establishing connection", aeskey, ke_duration);

    println!("Nonce sent: {:x?}", nonce);
    stream.write(&nonce).unwrap();

    get_video();

    //Gets video file and sends its size
    let video_file: Vec<u8> = fs::read("output.mkv").unwrap();
    let video_size = usize::to_ne_bytes(video_file.len()+16);
    stream.write(&video_size).unwrap();

    //Encrypts the video
    let encryption_start = Instant::now();
    let cipher = Aes256Gcm::new(&aeskey);
    let ciphertext = cipher.encrypt(&nonce, &video_file[..]).unwrap();
    let encryption_duration = encryption_start.elapsed();
    println!("{} bytes encrypted in {:?}", video_file.len()+16, encryption_duration);

    //Gets whether or other side is ready
    let mut confirm_buffer: Vec<u8> = vec![0; 1];
    stream.read(&mut confirm_buffer).unwrap();

    //Sends the encrypted data in parts
    let parts = (video_file.len()+16).div_ceil(65536);
    println!("Sending chunk {}/{}", 1, parts);
    stream.write(&ciphertext[0..65536]).unwrap();
    let data_start = Instant::now();
    if confirm_buffer[0] == 1 {
        for i in 1..parts-1 {
            let start = (i as u32)*65535;
            let end = start+65535;

            println!("Sending part {}/{}", i+1, parts);

            stream.write(&ciphertext[(start as usize)..(end as usize)]).unwrap();
        }
        let start = (parts-1)*65535;
        println!("Sending chunk {}/{}", parts, parts);
        stream.write(&ciphertext[start..video_file.len()+16]).unwrap();
        let data_duration = data_start.elapsed();
        println!("{} bytes sent in {:?}", video_file.len()+16, data_duration);
    }

    println!("Done");
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
            TermKey::Char('q') => break,
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