use ascon_aead::{aead::Aead, aead::KeyInit, Key, Nonce, Ascon128};
use ed25519_dalek::{Keypair, PublicKey, Signature, Signer, Verifier};
use ring::agreement::{EphemeralPrivateKey, UnparsedPublicKey, X25519};
use ring::rand::SystemRandom;
use ring::agreement;
use rand::Rng;
use std::io::{self, BufReader, Read, Write};
use std::net::TcpStream;
use std::thread;
use std::time::Instant;

// Generate X25519 keypair
fn generate_keypair() -> (EphemeralPrivateKey, Vec<u8>) {
    let rng = SystemRandom::new();
    let private_key = EphemeralPrivateKey::generate(&X25519, &rng).expect("Failed to generate key");
    let public_key = private_key.compute_public_key().expect("Failed to compute public key");
    (private_key, public_key.as_ref().to_vec())
}

// Derive shared secret
fn derive_shared_secret(private_key: EphemeralPrivateKey, peer_public_key: &[u8]) -> Vec<u8> {
    let peer_key = UnparsedPublicKey::new(&X25519, peer_public_key);
    agreement::agree_ephemeral(
        private_key,
        &peer_key,
        ring::error::Unspecified,
        |shared_secret| Ok(shared_secret.to_vec()),
    )
    .expect("Key agreement failed")
}

fn main() {
    let start_key_exchange = Instant::now();
    let (private_key, public_key) = generate_keypair();
    let ed25519_keypair = Keypair::generate(&mut rand::rngs::OsRng);

    let stream = TcpStream::connect("192.168.170.166:12345").expect("Failed to connect to the server");
    println!("Connected to the server!");

    let mut reader = BufReader::new(stream.try_clone().expect("Failed to clone stream"));
    let mut writer = stream.try_clone().expect("Failed to clone writer");

    writer.write_all(&public_key).expect("Failed to send X25519 public key");
    writer
        .write_all(ed25519_keypair.public.as_bytes())
        .expect("Failed to send Ed25519 public key");
    writer.flush().expect("Failed to flush stream");

    let mut peer_public_key = vec![0u8; 32];
    reader.read_exact(&mut peer_public_key).expect("Failed to read X25519 public key");

    let mut peer_ed25519_public_key_bytes = vec![0u8; 32];
    reader
        .read_exact(&mut peer_ed25519_public_key_bytes)
        .expect("Failed to read Ed25519 public key");
    let peer_ed25519_public_key =
        PublicKey::from_bytes(&peer_ed25519_public_key_bytes).expect("Invalid Ed25519 public key");

    let shared_secret = derive_shared_secret(private_key, &peer_public_key);
    let truncated_secret = shared_secret[..16].to_vec(); // Truncate to 16 bytes
    let boxed_truncated_secret = truncated_secret.into_boxed_slice(); // Box the data
    let encryption_key_data: &'static [u8] = Box::leak(boxed_truncated_secret); // Leak to `'static` lifetime
    let encryption_key = Key::<Ascon128>::from_slice(encryption_key_data);
    let cipher = Ascon128::new(&encryption_key);

    let elapsed_key_exchange = start_key_exchange.elapsed();
    println!("Key exchange time: {:.2?}", elapsed_key_exchange);

    thread::spawn(move || {
        let cipher_thread = Ascon128::new(&encryption_key);
        loop {
            let mut buffer = vec![0u8; 2048];
            match reader.read(&mut buffer) {
                Ok(bytes_read) => {
                    if bytes_read == 0 {
                        println!("Connection closed by server.");
                        break;
                    }
                    let nonce = Nonce::<Ascon128>::from_slice(&buffer[..16]);
                    let ciphertext = &buffer[16..bytes_read];

                    let start_decryption = Instant::now();
                    match cipher_thread.decrypt(nonce, ciphertext) {
                        Ok(decrypted_message) => {
                            let elapsed_decryption = start_decryption.elapsed();
                            println!("Decryption time: {:.2?}", elapsed_decryption);

                            if decrypted_message.len() < 64 {
                                eprintln!("Invalid message: too short for a valid signature");
                                continue;
                            }
                            let (signature_bytes, message_bytes) =
                                decrypted_message.split_at(64);
                            let signature = Signature::from_bytes(signature_bytes)
                                .expect("Invalid signature");
                            if peer_ed25519_public_key
                                .verify(message_bytes, &signature)
                                .is_ok()
                            {
                                let message = String::from_utf8_lossy(message_bytes);
                                println!("Received: {}", message);
                            } else {
                                eprintln!("Signature verification failed!");
                            }
                        }
                        Err(_) => eprintln!("Decryption failed!"),
                    }
                }
                Err(e) => {
                    eprintln!("Failed to read from stream: {}", e);
                    break;
                }
            }
        }
    });

    let stdin = io::stdin();
    let mut input = String::new();
    loop {
        print!("You: ");
        io::stdout().flush().unwrap();
        input.clear();
        stdin.read_line(&mut input).unwrap();
        if input.trim() == "exit" {
            println!("Closing connection...");
            break;
        }

        let signature = ed25519_keypair.sign(input.trim().as_bytes());
        let mut signed_message = Vec::new();
        signed_message.extend_from_slice(signature.as_ref());
        signed_message.extend_from_slice(input.trim().as_bytes());

        let mut rng = rand::thread_rng();
        let mut nonce_bytes = [0u8; 16];
        rng.fill(&mut nonce_bytes);
        let nonce = Nonce::<Ascon128>::from_slice(&nonce_bytes);

        let start_encryption = Instant::now();
        match cipher.encrypt(nonce, signed_message.as_slice()) {
            Ok(encrypted_message) => {
                let elapsed_encryption = start_encryption.elapsed();
                println!("Encryption time: {:.2?}", elapsed_encryption);

                let mut full_message = Vec::new();
                full_message.extend_from_slice(nonce_bytes.as_ref());
                full_message.extend_from_slice(&encrypted_message);

                writer.write_all(&full_message).expect("Failed to send message");
                writer.flush().expect("Failed to flush stream");
            }
            Err(_) => eprintln!("Encryption failed!"),
        }
    }
}