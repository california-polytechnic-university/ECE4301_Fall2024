use std::io::prelude::*;
use std::io::Read;
use std::fs;
use std::fs::File;
use std::net::TcpStream;
use std::time::{Duration, Instant};

use sec1::LineEnding::LF;
use rsa::{Pkcs1v15Encrypt, RsaPrivateKey, RsaPublicKey};
use rsa::pkcs8::EncodePublicKey;
use aes_gcm::{
    aead::{Aead, KeyInit},
    Aes256Gcm, Nonce, Key
};

fn main() {

    //Set up RSA by generating key pair
    let rsa_start = Instant::now();
    let mut rng = rand::thread_rng();
    let bits = 2048;
    let priv_key = RsaPrivateKey::new(&mut rng, bits).expect("failed to generate a key");
    let pub_key = RsaPublicKey::from(&priv_key);
    let rsa_duration = rsa_start.elapsed();
    println!("RSA key pair generated in {:?}", rsa_duration);

    //Gets public key into vector to send (Better method probably exists)
    pub_key.write_public_key_pem_file("key.pem", LF);
    let mut f = File::open("key.pem").unwrap();
    let mut pubkey_buffer = vec![0; f.metadata().unwrap().len() as usize];
    f.read(&mut pubkey_buffer[..]).unwrap();

    //Connects to the other device
    let mut stream = TcpStream::connect("192.168.6.4:7878").unwrap();
    let ke_start = Instant::now();

    //Sends the public key
    stream.write(&pubkey_buffer[..]).unwrap();
    println!("RSA public key sent");

    //Receives the encrypted AES key
    let mut aeskey_buffer = [0; 256];
    stream.read(&mut aeskey_buffer).unwrap();
    println!("Encrypted AES key received: {:x?}", aeskey_buffer);

    //Decrypts the AES key using the private RSA key
    let dec_data = priv_key.decrypt(Pkcs1v15Encrypt, &aeskey_buffer).expect("failed to decrypt");
    let dec_key = Key::<Aes256Gcm>::from_slice(&dec_data);
    let ke_duration = ke_start.elapsed();
    println!("Decrypted AES key: {:x}, {:?} since connection established", dec_key, ke_duration);

    //Receives the nonce
    let mut nonce_buffer: Vec<u8> = vec![0; 12];
    stream.read(&mut nonce_buffer).unwrap();
    let nonce = Nonce::from_slice(&nonce_buffer);
    println!("Nonce received: {:x?}", nonce);

    println!("Waiting for video to be generated");

    //Gets the size of the data being sent
    let mut size_buffer: Vec<u8> = vec![0; 8];
    stream.read(&mut size_buffer).unwrap();
    let size: [u8; 8] = size_buffer.try_into().unwrap();

    //Confirms ready to receives data
    let confirm: Vec<u8> = vec![1; 1];
    stream.write(&confirm).unwrap();

    //Creates a buffer to receive data, receives the data in parts
    let mut video_buffer: Vec<u8> = vec![0; usize::from_ne_bytes(size)];
    let parts = (usize::from_ne_bytes(size) as u32).div_ceil(65536);
    let data_start = Instant::now();
    stream.read(&mut video_buffer[0..65536]).unwrap();
    println!("Received part {}/{}", 1, parts);
    let mut ready_buffer: Vec<u8> = vec![0; 1];
    for i in 1..parts-1 {
        let start = (i as u32)*65535;
        let end = start+65535;

        stream.read(&mut video_buffer[(start as usize)..(end as usize)]).unwrap();
        println!("Received part {}/{}", i, parts);

    }
    let start = (parts-1)*65535;
    stream.read(&mut video_buffer[(start as usize)..(usize::from_ne_bytes(size))]).unwrap();
    println!("Received part {}/{}", parts, parts);
    let data_duration = data_start.elapsed();
    println!("{} bytes received in {:?}", usize::from_ne_bytes(size), data_duration);

    //Decrypts the received data
    println!("Decrypting data");
    let decryption_start = Instant::now();
    let cipher = Aes256Gcm::new(&dec_key);
    let plaintext = cipher.decrypt(&nonce, &video_buffer[..]).unwrap();
    let decryption_duration = decryption_start.elapsed();
    println!("{} bytes decrypted in {:?}", usize::from_ne_bytes(size), decryption_duration);

    //Writes decrypted data to file
    let mut file = fs::OpenOptions::new().create(true).write(true).open("output.mkv").unwrap();
    file.write_all(&plaintext).expect("Couldn't write to file");
    println!("Data decrypted and saved as output.mkv");

}