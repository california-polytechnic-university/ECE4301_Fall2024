import socket
import cv2
import numpy as np
import struct
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
import random
import time

# Generate RSA Key Pair
def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    return private_key, public_key

# Decrypt RSA-encrypted data
def rsa_decrypt(private_key, encrypted_data):
    return private_key.decrypt(
        encrypted_data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

# Perform Diffie-Hellman Key Exchange
def diffie_hellman(p, g, private_value):
    """Perform Diffie-Hellman key exchange."""
    public_value = pow(g, private_value, p)
    return public_value

# AES Decryption Setup
def create_aes_cipher(key, iv):
    return Cipher(algorithms.AES(key), modes.CFB(iv))

# Server Configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 5000

# Generate RSA keys for secure DH parameter exchange
private_key, public_key = generate_rsa_keys()

# Initialize server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1048576)  # Increase buffer size
server.bind((HOST, PORT))
server.listen(1)
print(f"Server started and listening on {HOST}:{PORT}")

try:
    while True:
        print("Waiting for a connection...")
        connection, address = server.accept()
        print(f"Connected by {address}")

        # Key exchange timing
        key_exchange_start = time.time()

        # 1. Exchange RSA Public Keys
        server_public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        connection.sendall(server_public_key_bytes)

        client_public_key_bytes = connection.recv(4096)
        client_public_key = serialization.load_pem_public_key(client_public_key_bytes)

        # 2. Generate DH Parameters
        print("Generating DH parameters...")
        p = 23  # Example smaller prime for testing
        g = 5  # Example generator
        server_private_value = random.randint(2, p - 2)

        # Encrypt and send DH parameters
        dh_params = f"{p},{g}".encode()
        encrypted_dh_params = client_public_key.encrypt(
            dh_params,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        connection.sendall(encrypted_dh_params)

        # Compute and send the server's DH public value
        server_dh_public = diffie_hellman(p, g, server_private_value)
        encrypted_server_dh_public = client_public_key.encrypt(
            str(server_dh_public).encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        connection.sendall(encrypted_server_dh_public)

        # Receive and decrypt the client's DH public value
        encrypted_client_dh_public = connection.recv(4096)
        client_dh_public = int(rsa_decrypt(private_key, encrypted_client_dh_public))

        # Compute the shared secret
        shared_secret = pow(client_dh_public, server_private_value, p)
        aes_key = shared_secret.to_bytes(32, "big")[:32]  # Use first 32 bytes as AES key

        # Receive IV from the client
        iv = connection.recv(16)

        # Key exchange completed
        key_exchange_time = (time.time() - key_exchange_start) * 1000  # Convert to milliseconds
        print(f"Key Exchange Time: {key_exchange_time:.2f} ms")

        print("Shared secret established. Starting video stream decryption.")

        # Initialize AES cipher
        cipher = create_aes_cipher(aes_key, iv)
        decryptor = cipher.decryptor()

        # Process and display frames
        frame_count = 0
        start_time = time.time()

        while True:
            # Receive frame length
            frame_length_bytes = connection.recv(4)
            if not frame_length_bytes:
                break
            frame_length = struct.unpack("!I", frame_length_bytes)[0]

            # Receive the full encrypted frame
            encrypted_frame = b""
            while len(encrypted_frame) < frame_length:
                packet = connection.recv(frame_length - len(encrypted_frame))
                if not packet:
                    break
                encrypted_frame += packet

            # Decrypt the frame
            decryption_start = time.time()
            decrypted_frame = decryptor.update(encrypted_frame)
            decryption_time = (time.time() - decryption_start) * 1000  # Convert to milliseconds

            # Convert to numpy array and display
            frame_array = np.frombuffer(decrypted_frame, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

            # Resize frame to fit screen
            frame = cv2.resize(frame, (640, 480))

            # Update metrics
            frame_count += 1
            elapsed_time = time.time() - start_time
            fps = frame_count / elapsed_time

            print(f"Decryption Time: {decryption_time:.2f} ms | Total Frames: {frame_count} | FPS: {fps:.2f}")

            cv2.imshow("Video Stream", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        connection.close()
        print("Connection closed.")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    server.close()
    cv2.destroyAllWindows()
    print("Server shut down.")
