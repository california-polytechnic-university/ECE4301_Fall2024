use std::time::Instant;
use aes::Aes256;
use block_modes::{block_padding::Pkcs7, BlockMode, Cbc};
use num_bigint::{BigUint, RandBigInt};
use opencv::prelude::*;
use opencv::{highgui, imgcodecs};
use rand::rngs::OsRng;
use sha2::{Digest, Sha256};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpListener;

type Aes256Cbc = Cbc<Aes256, Pkcs7>;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let port = 8080;

    // Start the server
    let listener = TcpListener::bind(format!("0.0.0.0:{}", port)).await?;
    println!("Receiver is listening on port {}.", port);

    loop {
        let (mut stream, _) = listener.accept().await?;
        println!("Sender connected.");

        // key exchange AES key
        let key = perform_key_exchange(&mut stream).await?;

        // Receive and display
        receive_and_display_frames(&key, &mut stream).await?;
    }
}

async fn perform_key_exchange(
    stream: &mut tokio::net::TcpStream,
) -> Result<[u8; 32], Box<dyn std::error::Error>> {
    use std::convert::TryInto;

    let start_time = Instant::now();
//Diffie-Hellman
    let p_hex = "\
        FFFFFFFF FFFFFFFF C90FDAA2 2168C234 C4C6628B 80DC1CD1 \
        29024E08 8A67CC74 020BBEA6 3B139B22 514A0879 8E3404DD \
        EF9519B3 CD3A431B 302B0A6D F25F1437 4FE1356D 6D51C245 \
        E485B576 625E7EC6 F44C42E9 A637ED6B 0BFF5CB6 F406B7ED \
        EE386BFB 5A899FA5 AE9F2411 7C4B1FE6 49286651 ECE65381 \
        FFFFFFFF FFFFFFFF";

    let p = BigUint::parse_bytes(&p_hex.replace(" ", "").as_bytes(), 16).unwrap();
    let g = BigUint::from(2u32);

    // Receive public key
    let mut length_bytes = [0u8; 4];
    stream.read_exact(&mut length_bytes).await?;
    let sender_key_length = u32::from_be_bytes(length_bytes) as usize;
    let mut sender_public_key_bytes = vec![0u8; sender_key_length];
    stream.read_exact(&mut sender_public_key_bytes).await?;
    let sender_public_key = BigUint::from_bytes_be(&sender_public_key_bytes);

    // Generate
    let mut rng = OsRng;
    let private_key = rng.gen_biguint(256);
    let public_key = g.modpow(&private_key, &p);
    let public_key_bytes = public_key.to_bytes_be();

    //public
    let key_length = public_key_bytes.len() as u32;
    stream.write_all(&key_length.to_be_bytes()).await?;
    stream.write_all(&public_key_bytes).await?;

    // secret
    let shared_secret = sender_public_key.modpow(&private_key, &p);
    // AES
    let shared_secret_bytes = shared_secret.to_bytes_be();
    let mut hasher = Sha256::new();
    hasher.update(&shared_secret_bytes);
    let result = hasher.finalize();
    let key: [u8; 32] = result.as_slice()[..32].try_into().unwrap();

    let duration = start_time.elapsed();
    println!("Key exchange completed in {:?}", duration);

    Ok(key)
}

async fn receive_and_display_frames(
    key: &[u8; 32],
    stream: &mut tokio::net::TcpStream,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut total_data_received: usize = 0;
    let mut frame_count = 0;
    let start_time = Instant::now();

    loop {
        let mut length_bytes = [0u8; 4];
        if let Err(_) = stream.read_exact(&mut length_bytes).await {
            println!("Connection closed by sender.");
            break;
        }
        let frame_length = u32::from_be_bytes(length_bytes) as usize;
        //IV
        let mut iv = [0u8; 16];
        stream.read_exact(&mut iv).await?;
        // Receive
        let mut encrypted_frame = vec![0u8; frame_length];
        stream.read_exact(&mut encrypted_frame).await?;
        // Decrypt
        let decryption_start = Instant::now();
        let decrypted_frame = match decrypt_frame(&encrypted_frame, key, &iv) {
            Ok(data) => data,
            Err(e) => {
                eprintln!("Failed to decrypt frame: {}", e);
                continue;
            }
        };
        let decryption_duration = decryption_start.elapsed();
        let buffer = opencv::core::Vector::<u8>::from(decrypted_frame); 
        let mat = imgcodecs::imdecode(&buffer, imgcodecs::IMREAD_GRAYSCALE)?;
        if mat.size()?.width == 0 || mat.size()?.height == 0 {
            eprintln!("Failed to decode image.");
            continue;
        }

        // Display the frame
        highgui::imshow("Live Stream", &mat)?;

        total_data_received += frame_length as usize + iv.len() + 4;
        frame_count += 1;

        let elapsed = start_time.elapsed().as_secs_f64();
        if elapsed > 0.0 {
            let fps = frame_count as f64 / elapsed;
            let bandwidth = total_data_received as f64 / elapsed / 1024.0; // KB/s
            println!(
                "Frame {}: Decrypted in {:?}, FPS: {:.2}, Bandwidth: {:.2} KB/s",
                frame_count, decryption_duration, fps, bandwidth
            );
        }

        if highgui::wait_key(1)? == 27 {
            // Exit
            println!("Exit signal received. Closing receiver.");
            break;
        }
    }

    Ok(())
}

fn decrypt_frame(
    ciphertext: &[u8],
    key: &[u8; 32],
    iv: &[u8; 16],
) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let cipher = Aes256Cbc::new_from_slices(key, iv)?;
    let decrypted_data = cipher.decrypt_vec(ciphertext)?;
    Ok(decrypted_data)
}
