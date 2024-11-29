import cv2
import socket
import struct
import pickle
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import hashlib
import time


# Generate RSA Keys
def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key

# Serialize Public Key to PEM format
def serialize_public_key(public_key):
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

# Deserialize Public Key from PEM format
def deserialize_public_key(pem_data):
    return serialization.load_pem_public_key(pem_data)

# Calculate SHA-256 checksum
def calculate_checksum(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()

# Main Server Logic
def server():
    # Step 1: Generate RSA keys for key exchange
    private_key, public_key = generate_rsa_keys()

    # Step 2: Start a socket server for communication
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 7878))
    server_socket.listen(1)
    print("Server listening on port 7878...")

    conn, addr = server_socket.accept()
    print(f"Connection from {addr}")

    # Step 3: Exchange RSA public keys
    server_public_key_pem = serialize_public_key(public_key)
    conn.sendall(server_public_key_pem)  # Send server's public key
    print("Server public key sent.")

    client_public_key_pem = conn.recv(1024)  # Receive client's public key
    client_public_key = deserialize_public_key(client_public_key_pem)
    print("Received client's public key.")

    # Step 4: Generate AES-GCM key and nonce, encrypt them using the client's public key, and send
    aes_key = os.urandom(32)  # 256-bit AES key
    aes_nonce = os.urandom(12)  # 96-bit nonce for AES-GCM
    print(f"Generated AES key: {aes_key.hex()}")
    print(f"Generated AES nonce: {aes_nonce.hex()}")

    encrypted_aes_key_nonce = client_public_key.encrypt(
        aes_key + aes_nonce,  # Concatenate key and nonce
        padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    conn.sendall(encrypted_aes_key_nonce)
    print("Encrypted AES key and nonce sent to client.")

    # Step 5: Start video streaming with AES-GCM encryption
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("Error: Camera could not be opened.")
        return

    print("Camera opened successfully.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture video frame.")
                break

            print("Captured a video frame.")

            # Serialize the frame
            data = pickle.dumps(frame)
            original_checksum = calculate_checksum(data)
            print(f"Original checksum: {original_checksum}")

            # Encrypt the video frame using AES-GCM
            aes_cipher = Cipher(
                algorithms.AES(aes_key),
                modes.GCM(aes_nonce),
                backend=default_backend(),
            )
            encryptor = aes_cipher.encryptor()
            encrypted_data = encryptor.update(data) + encryptor.finalize()
            tag = encryptor.tag  # GCM tag for authentication
            encrypted_checksum = calculate_checksum(encrypted_data)
            print(f"Encrypted checksum: {encrypted_checksum}")
            print(f"GCM Authentication Tag: {tag.hex()}")

            data_size = len(encrypted_data)
            print(f"Encrypted frame size: {data_size} bytes")

            # Send encrypted frame size (4 bytes, network byte order)
            conn.sendall(struct.pack("!I", data_size))

            # Send GCM tag (16 bytes) for authentication
            conn.sendall(tag)

            # Send the encrypted frame data in chunks
            for i in range(0, data_size, 4096):
                conn.sendall(encrypted_data[i:i+4096])

            print("Encrypted frame sent in chunks.")

    except Exception as e:
        print(f"Exception occurred: {e}")

    finally:
        cap.release()
        conn.close()
        server_socket.close()
        print("Server shut down.")


if __name__ == "__main__":
    server()
