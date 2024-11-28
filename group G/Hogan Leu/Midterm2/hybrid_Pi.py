from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
import os

def encrypt_file(aes_key, input_file_path, output_file_path):
    # Read the input video file
    with open(input_file_path, 'rb') as infile:
        data = infile.read()

    # Generate a random IV
    iv = os.urandom(16)

    # Create AES cipher in CBC mode
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    encryptor = cipher.encryptor()

    # Pad the data and encrypt
    padder = PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Write IV and encrypted data to output file
    with open(output_file_path, 'wb') as outfile:
        outfile.write(iv + encrypted_data)

    print(f"File encrypted successfully. Output saved to {output_file_path}.")

def main():
    # Generate a random AES key
    aes_key = os.urandom(32)
    
    # Save the AES key securely
    with open('/home/savehope7777/aes_key.bin', 'wb') as key_file:
        key_file.write(aes_key)
    print("AES key generated and saved.")

    # Define file paths
    input_file = '/home/savehope7777/IMG_5585.mp4'
    output_file = '/home/savehope7777/encrypted_5585.enc'

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found!")
        return

    # Encrypt the video file
    encrypt_file(aes_key, input_file, output_file)

if __name__ == "__main__":
    main()




