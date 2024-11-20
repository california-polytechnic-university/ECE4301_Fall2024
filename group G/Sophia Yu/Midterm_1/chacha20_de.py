from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

def decrypt_file(encrypted_file, output_file, key, nonce):
    # Open the encrypted file in binary mode
    with open(encrypted_file, 'rb') as f_in:
        ciphertext = f_in.read()

    # Initialize the ChaCha20 cipher for decryption
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
    decryptor = cipher.decryptor()

    # Decrypt the data
    plaintext = decryptor.update(ciphertext)

    # Write the decrypted content to the output file
    with open(output_file, 'wb') as f_out:
        f_out.write(plaintext)

    print(f"File '{encrypted_file}' decrypted to '{output_file}'.")

# Specify output files for decryption
decrypted_file = '/home/user01/decrypted_video.mp4'
encrypted_file = '/home/user01/encrypted_video.mp4'

# Decrypt the file
key = b'\xed\x1f\x8ek\xf7\xf3\xaf\n\x9cS#nuh\x1b\xfa\x05Q\xd5\\\xc2;}\xd2\xd0\x8b\x0e\xae\x89\xbc|I'
nonce = b'\t<\xaa\x04\xf3\xc5\x89\xdc\xc0]-X\x8ef.2'
decrypt_file(encrypted_file, decrypted_file, key, nonce)
