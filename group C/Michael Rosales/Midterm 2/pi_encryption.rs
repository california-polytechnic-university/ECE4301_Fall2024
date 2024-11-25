use std::time::{Duration, Instant};

use aes::Aes256;
use block_modes::{block_padding::Pkcs7, BlockMode, Cbc};
use num_bigint::{BigUint, RandBigInt};
use opencv::{highgui, imgcodecs, imgproc, videoio};
use opencv::core::Mat;
use opencv::prelude::{VideoCaptureTrait, VideoCaptureTraitConst, MatTraitConst, VectorToVec};
use rand::rngs::OsRng;
use sha2::{Digest, Sha256};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;


type Aes256Cbc = Cbc<Aes256, Pkcs7>;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let receiver_ip = "192.168.4.26";//laptop ip
    let port = 8080;
 // Connect
    let mut stream = TcpStream::connect(format!("{}:{}", receiver_ip, port)).await?;
    println!("Connected to receiver.");

    //key exchange  AES key
    let key = perform_key_exchange(&mut stream).await?;
    // Capture and send
    capture_and_send_frames(&key, &mut stream).await?;
    Ok(())
}

async fn perform_key_exchange(
    stream: &mut TcpStream,
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
    // Generate private and public keys
    let mut rng = OsRng;
    let private_key = rng.gen_biguint(256);
    let public_key = g.modpow(&private_key, &p);
    let public_key_bytes = public_key.to_bytes_be();
    // Send public key
    let key_length = public_key_bytes.len() as u32;
    stream.write_all(&key_length.to_be_bytes()).await?;
    stream.write_all(&public_key_bytes).await?;

    // Receive public key
    let mut length_bytes = [0u8; 4];
    stream.read_exact(&mut length_bytes).await?;
    let receiver_key_length = u32::from_be_bytes(length_bytes) as usize;
    let mut receiver_public_key_bytes = vec![0u8; receiver_key_length];
    stream.read_exact(&mut receiver_public_key_bytes).await?;
    let receiver_public_key = BigUint::from_bytes_be(&receiver_public_key_bytes);

    // Compute secret
    let shared_secret = receiver_public_key.modpow(&private_key, &p);

    // Derive AES 
    let shared_secret_bytes = shared_secret.to_bytes_be();
    let mut hasher = Sha256::new();
    hasher.update(&shared_secret_bytes);
    let result = hasher.finalize();
    let key: [u8; 32] = result.as_slice()[..32].try_into().unwrap();
    let duration = start_time.elapsed();
    println!("Key exchange completed in {:?}", duration);
    Ok(key)
}

async fn capture_and_send_frames(
    key: &[u8; 32],
    stream: &mut TcpStream,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut cam = videoio::VideoCapture::new(0, videoio::CAP_V4L2)?;
    // camera properties
    cam.set(videoio::CAP_PROP_FRAME_WIDTH, 320.0)?;
    cam.set(videoio::CAP_PROP_FRAME_HEIGHT, 240.0)?;

    if !cam.is_opened()? {
        panic!("Unable to open cam");
    }
    let mut total_data_sent: usize = 0;
    let mut frame_count = 0;
    let start_time = Instant::now();

    loop {
        let mut frame = Mat::default();
        cam.read(&mut frame)?;

        if frame.empty() {
            continue;
        }
        // grayscale
        let mut gray_frame = Mat::default();
        imgproc::cvt_color(&frame, &mut gray_frame, imgproc::COLOR_BGR2GRAY, 0)?;
        // Encode frame
        let mut buf = opencv::core::Vector::new();
        let params = opencv::core::Vector::<i32>::new();
        imgcodecs::imencode(".jpg", &gray_frame, &mut buf, &params)?;

        let frame_bytes = buf.to_vec();
        // Encrypt the frame
        let encryption_start = Instant::now();
        let iv = rand::random::<[u8; 16]>();
        let cipher = Aes256Cbc::new_from_slices(key, &iv)?;
        let ciphertext = cipher.encrypt_vec(&frame_bytes);
        let encryption_duration = encryption_start.elapsed();

        // Send the length of the encrypted frame
        let frame_length = ciphertext.len() as u32;
        stream.write_all(&frame_length.to_be_bytes()).await?;

        // IV
        stream.write_all(&iv).await?;

        // Send frame
        stream.write_all(&ciphertext).await?;

        total_data_sent += frame_length as usize + iv.len() + 4;
        frame_count += 1;

        let elapsed = start_time.elapsed().as_secs_f64();
        if elapsed > 0.0 {
            let fps = frame_count as f64 / elapsed;
            let bandwidth = total_data_sent as f64 / elapsed / 1024.0; // KB/s
            println!(
                "Frame {}: Encrypted in {:?}, FPS: {:.2}, Bandwidth: {:.2} KB/s",
                frame_count, encryption_duration, fps, bandwidth
            );
        }
        // Control frame rate 
        tokio::time::sleep(Duration::from_millis(33)).await;

        // Break 'Esc'
        if highgui::wait_key(1)? == 27 {
            println!("Exit signal received. Closing sender.");
            break;
        }
    }
    Ok(())
}

