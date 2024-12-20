from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

key = os.urandom(32)
nonce = os.urandom(32)


def encrypt_file(input_file, output_file, key, nonce):

	# open the file and save as plaintext
	with open(input_file, 'rb') as f_in:
		plaintext = f_in.read()
	print(f"Read{len(plaintext)} bytes from '{input_file}'.")
	
	# Initialize the ChaCha20 cipher
	cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
	encryptor = cipher.encryptor()

    # Encrypt the data
	ciphertext = encryptor.update(plaintext)
    
    # Write the encrypted content to the output file
	with open(output_file, 'wb') as f_out:
		f_out.write(ciphertext)

	print(f"File '{input_file}' encrypted to '{output_file}'.")
    
# Generate a random 32-byte key and a 12-byte nonce
# key = os.urandom(32)  # ChaCha20 requires a 256-bit (32-byte) key
# nonce = os.urandom(16)  # ChaCha20 uses a 96-bit (13-byte) nonce

key = b'\xed\x1f\x8ek\xf7\xf3\xaf\n\x9cS#nuh\x1b\xfa\x05Q\xd5\\\xc2;}\xd2\xd0\x8b\x0e\xae\x89\xbc|I'
nonce = b'\t<\xaa\x04\xf3\xc5\x89\xdc\xc0]-X\x8ef.2'
# Specify input and output files
input_file = '/home/sophia/IMG_2853.mp4'
encrypted_file = '/home/sophia/encrypted_video.mp4'

# Encrypt the file
encrypt_file(input_file, encrypted_file, key, nonce)
print("key =" ,key)
print("nonce = " ,nonce)
