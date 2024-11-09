use minifb::{Window, WindowOptions};
use reqwest::Client;
use chacha20::ChaCha20;
use chacha20::cipher::{NewCipher, StreamCipher};
use cipher::generic_array::GenericArray;
use std::error::Error;
use std::io::Cursor;
use image::io::Reader as ImageReader;
use std::time::Duration;
use tokio::time::sleep;

const KEY: [u8; 32] = *b"Thirtytwo very very secret bytes";
const NONCE: [u8; 16] = *b"These are sixtee";

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let client = Client::builder()
        .timeout(Duration::from_secs(20))
        .build()?;

    let url = "http://192.168.101.176:8000/stream2.mjpg";

    let mut window = Window::new("Video Feed", 640, 480, WindowOptions::default())
        .expect("Failed to create window");

    let mut buffer = vec![0; 640 * 480];

    loop {
        println!("Sending request to {}", url);
        let mut response = client.get(url).send().await?;
        println!("Response received");

        while let Some(chunk) = response.chunk().await?{
            println!("Chunk received");

            let key = GenericArray::from_slice(&KEY);
            let nonce = GenericArray::from_slice(&NONCE[..12]);
            let mut cipher = ChaCha20::new(key, nonce);

            let mut decrypted_frame = chunk.to_vec();
            cipher.apply_keystream(&mut decrypted_frame);
            println!("Decrypted frame size: {}", decrypted_frame.len());
            println!("Decrypted frame first bytes: {:?}", &decrypted_frame[..4]);

            let cursor = Cursor::new(decrypted_frame);
            let img = match ImageReader::new(cursor).with_guessed_format()?.decode() { // This line might be the problem.
                Ok(img) => img,
                Err(e) => {
                    println!("Failed to decode image: {}", e);
                    continue;
                }
            };
            println!("Image decoded");

            let rgb_image = img.to_rgb8();
            for (i, pixel) in rgb_image.pixels().enumerate() {
                let [r, g, b] = pixel.0;
                buffer[i] = ((r as u32) << 16) | ((g as u32) << 8) | (b as u32);
            }

            window.update_with_buffer(&buffer, 640, 480)
                .expect("Failed to update window buffer");
            println!("Frame displayed");

            sleep(Duration::from_millis(100)).await; // Adjust the sleep time as needed
        }

        if !window.is_open() {
            break;
        }
    }
    Ok(())
}