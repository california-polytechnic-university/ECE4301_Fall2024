from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

import subprocess
import os
import time

def generate_and_save_keys():


    # generate private key
    PI_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # get private key
    PI_public_key = PI_private_key.public_key()

    # save as .pem
    # Save the private key as a .pem file
    with open("PI_private_key.pem", "wb") as private_file:
        private_file.write(
            PI_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    with open("PI_public_key.pem", "wb") as public_file:
        public_file.write(
            PI_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

    print(f"Keys generated and saved")

def sent_file(file_to_send):
    subprocess.run(f"scp /home/sophia/git_code/hybrid_crypto/{file_to_send} user01@192.168.4.21:/home/user01/git_file/python/RSA_DF_encrypto", shell=True, check=True)

def wait_public_key_to_read(target_file_path, interval):

    # Wait until the file arrives
    while not os.path.exists(target_file_path):
        print(f"Waiting for the file to arrive: {target_file_path}")
        time.sleep(interval)

    # File has arrived; load the public key
    with open(target_file_path, "rb") as key_file:
        public_key = serialization.load_pem_public_key(key_file.read())

    print(f"File {target_file_path} loaded successfully.")


    return public_key
        
def generate_shared_key(PI_random_value, LX_random_value):
    combined = PI_random_value + LX_random_value
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None, 
        info=b'shared secret'
    )
    return hkdf.derive(combined)

# Decryption function
def decrypt_file(shared_key, input_file_path, output_file_path):
    # Read the encrypted file
    with open(input_file_path, 'rb') as infile:
        data = infile.read()

    # Extract the IV (first 16 bytes) and the ciphertext
    iv = data[:16]
    ciphertext = data[16:]

    # Create AES cipher in CBC mode
    cipher = Cipher(algorithms.AES(shared_key), modes.CBC(iv))
    decryptor = cipher.decryptor()

    # Decrypt the data
    decrypted_padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    # Remove padding from the decrypted data
    unpadder = PKCS7(algorithms.AES.block_size).unpadder()
    decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()

    # Write the decrypted data to the output file
    with open(output_file_path, 'wb') as outfile:
        outfile.write(decrypted_data)

    print(f"File decrypted successfully. Output saved to {output_file_path}.")

# Encryption function
def encrypt_file(shared_key, input_file_path, output_file_path):
    # Generate a random IV (Initialization Vector)
    iv = os.urandom(16)

    # Create AES cipher in CBC mode
    cipher = Cipher(algorithms.AES(shared_key), modes.CBC(iv))
    encryptor = cipher.encryptor()

    # Read the input MP4 file
    with open(input_file_path, 'rb') as infile:
        data = infile.read()

    # Pad the data to make it a multiple of the block size
    padder = PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()

    # Encrypt the padded data
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Write the IV and encrypted data to the output file
    with open(output_file_path, 'wb') as outfile:
        outfile.write(iv + encrypted_data)

    print(f"File encrypted successfully. Output saved to {output_file_path}.")



def main():

    PI_random_value = os.urandom(32)
    # Step 1: Generate Host's RSA Key Pair
    generate_and_save_keys()
    
    # Step 2: Send Host's Public Key to PI
    sent_file("PI_public_key.pem")

    # Step 3: Wait for PI's Public Key
    LX_public_key = wait_public_key_to_read("/home/sophia/git_code/hybrid_crypto/LX_public_key.pem", 20)

    # Step 4: Encrypt Host's Random Value with LX's Public Key
    PI_encrypted_random_value = LX_public_key.encrypt(
        PI_random_value, 
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    with open("PI_encrypted_random_value.bin", "wb") as f:
        f.write(PI_encrypted_random_value)
        print("done")



    # Step 5: Send Encrypted Random Value to PI
    sent_file("PI_encrypted_random_value.bin")

    # Step 6: Wait for LX's Encrypted Random Value
    encrypted_random_value_path = "/home/sophia/git_code/hybrid_crypto/LX_encrypted_random_value.bin"

    while not os.path.exists(encrypted_random_value_path):
        print("Waiting for encrypted random value...")
        time.sleep(5)


    # Load the encrypted random value
    with open(encrypted_random_value_path, "rb") as f:
        LX_encrypted_random_value = f.read()

    # read own private value to Decrypt the random value
    PI_private_key_path = "/home/sophia/git_code/hybrid_crypto/PI_private_key.pem"
    with open(PI_private_key_path, "rb") as f:
        PI_private_key = serialization.load_pem_private_key(
            f.read(),
            password=None
        )

    LX_random_value = PI_private_key.decrypt(
        LX_encrypted_random_value,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Step 8: Derive AES Key from PI's Random Value
    aes_key = generate_shared_key(PI_random_value, LX_random_value)

    # Step 11: Receive and Decrypt Video from PI
    input_file = '/home/sophia/IMG_2853.mp4'
    output_file = 'encrypted_video.enc'
    encrypt_file(aes_key, input_file, output_file)
    
    sent_file("encrypted_video.enc")

if __name__ == "__main__":
    main()
