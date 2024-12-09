use std::sync::{Arc, Mutex};
use std::net::{TcpListener, TcpStream};
use std::thread;
use std::io::{BufReader, Read, Write};

use ascon_aead::{aead::Aead, aead::KeyInit, Key, Nonce, Ascon128};
use ed25519_dalek::{Keypair, PublicKey, Signature, Verifier};
use ring::agreement::{EphemeralPrivateKey, UnparsedPublicKey, X25519};
use ring::rand::SystemRandom;
use ring::agreement;
use rand::Rng;

// Generate X25519 keypair
fn generate_x25519_keypair() -> (EphemeralPrivateKey, Vec<u8>) {
    let rng = SystemRandom::new();
    let private_key = EphemeralPrivateKey::generate(&X25519, &rng).expect("Failed to generate key");
    let public_key = private_key.compute_public_key().expect("Failed to compute public key");
    (private_key, public_key.as_ref().to_vec())
}

// Derive shared secret using X25519
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

// Handle a single client connection
fn handle_client(
    mut stream: TcpStream,
    id: usize,
    shared_message_log: Arc<Mutex<Vec<String>>>,
    clients: Arc<Mutex<Vec<(TcpStream, Key<Ascon128>)>>>,
) {
    let (private_key, public_key) = generate_x25519_keypair();
    let ed25519_keypair = Keypair::generate(&mut rand::rngs::OsRng);

    // Send public keys to the client
    stream.write_all(&public_key).expect("Failed to send X25519 public key");
    stream
        .write_all(ed25519_keypair.public.as_bytes())
        .expect("Failed to send Ed25519 public key");
    stream.flush().expect("Failed to flush stream");

    // Receive client's public keys
    let mut peer_public_key = vec![0u8; 32];
    stream.read_exact(&mut peer_public_key).expect("Failed to read X25519 public key");
    let mut peer_ed25519_public_key_bytes = vec![0u8; 32];
    stream
        .read_exact(&mut peer_ed25519_public_key_bytes)
        .expect("Failed to read Ed25519 public key");
    let peer_ed25519_public_key = PublicKey::from_bytes(&peer_ed25519_public_key_bytes)
        .expect("Invalid Ed25519 public key");

    // Derive shared secret and generate encryption key
    let shared_secret = derive_shared_secret(private_key, &peer_public_key);
    let truncated_secret = shared_secret[..16].to_vec(); // Truncate to 16 bytes
    let encryption_key = Key::<Ascon128>::from_slice(&truncated_secret);

    // Add the client stream and encryption key to the active clients list
    {
        let mut clients_guard = clients.lock().unwrap();
        clients_guard.push((stream.try_clone().expect("Failed to clone client stream"), encryption_key.clone()));
    }

    let mut reader = BufReader::new(stream.try_clone().expect("Failed to clone stream"));

    // Handle incoming messages in a separate thread
    {
        let encryption_key = encryption_key.clone();
        let clients = Arc::clone(&clients);
        let shared_message_log = Arc::clone(&shared_message_log);

        thread::spawn(move || {
            let cipher_thread = Ascon128::new(&encryption_key);
            loop {
                let mut buffer = vec![0u8; 2048];
                match reader.read(&mut buffer) {
                    Ok(bytes_read) => {
                        if bytes_read == 0 {
                            println!("Client {} disconnected.", id);
                            break;
                        }
                        let nonce = Nonce::<Ascon128>::from_slice(&buffer[..16]);
                        match cipher_thread.decrypt(nonce, &buffer[16..bytes_read]) {
                            Ok(decrypted_message) => {
                                if decrypted_message.len() < 64 {
                                    eprintln!("Invalid message: too short for signature.");
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
                                    let message =
                                        String::from_utf8_lossy(message_bytes).to_string();
                                    let mut log = shared_message_log.lock().unwrap();
                                    log.push(format!("Client {}: {}", id, message));
                                    println!("Client {}: {}", id, message);

                                    // Broadcast the encrypted message to other clients
                                    let mut clients_guard = clients.lock().unwrap();
                                    for (client_stream, client_key) in clients_guard.iter_mut() {
                                        if client_stream.peer_addr().unwrap()
                                            != stream.peer_addr().unwrap()
                                        {
                                            let mut rng = rand::thread_rng();
                                            let mut nonce_bytes = [0u8; 16];
                                            rng.fill(&mut nonce_bytes); // Generate a unique nonce
                                            let nonce =
                                                Nonce::<Ascon128>::from_slice(&nonce_bytes);

                                            let client_cipher = Ascon128::new(client_key);

                                            // Include the signature in the encrypted message
                                            let mut signed_message = Vec::new();
                                            signed_message.extend_from_slice(signature_bytes);
                                            signed_message.extend_from_slice(message.as_bytes());

                                            let encrypted_message = client_cipher
                                                .encrypt(nonce, signed_message.as_slice());
                                            if let Ok(encrypted_data) = encrypted_message {
                                                let mut full_message = Vec::new();
                                                full_message.extend_from_slice(&nonce_bytes);
                                                full_message.extend_from_slice(&encrypted_data);

                                                client_stream
                                                    .write_all(&full_message)
                                                    .expect("Failed to forward message");
                                            } else {
                                                eprintln!(
                                                    "Encryption failed for client at {:?}",
                                                    client_stream.peer_addr()
                                                );
                                            }
                                        }
                                    }
                                } else {
                                    eprintln!("Signature verification failed for client {}.", id);
                                }
                            }
                            Err(_) => eprintln!("Decryption failed for client {}.", id),
                        }
                    }
                    Err(e) => {
                        eprintln!("Failed to read from client {}: {}", id, e);
                        break;
                    }
                }
            }
        });
    }
}

fn main() {
    let listener = TcpListener::bind("0.0.0.0:12345").expect("Failed to bind to address");
    println!("Server listening on port 12345...");

    let shared_message_log = Arc::new(Mutex::new(Vec::new()));
    let clients = Arc::new(Mutex::new(Vec::new())); // List of active clients and their keys
    let mut client_id = 0;

    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                let id = client_id;
                client_id += 1;
                println!("Client {} connected.", id);

                let shared_log = Arc::clone(&shared_message_log);
                let clients = Arc::clone(&clients);
                thread::spawn(move || {
                    handle_client(stream, id, shared_log, clients);
                });
            }
            Err(e) => eprintln!("Connection failed: {}", e),
        }
    }
}

