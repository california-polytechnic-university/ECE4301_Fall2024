import socket
import cv2
import numpy as np
import os
import struct
import random
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import time

# Generate RSA Key Pair
def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    return private_key, public_key

# RSA Encryption
def rsa_encrypt(public_key, data):
    return public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

# RSA Decryption
def rsa_decrypt(private_key, data):
    return private_key.decrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

# AES Encryption Setup
def create_aes_cipher(key, iv):
    return Cipher(algorithms.AES(key), modes.CFB(iv))

# Diffie-Hellman Key Exchange
def diffie_hellman(p, g, private_value):
    """Perform Diffie-Hellman key exchange."""
    public_value = pow(g, private_value, p)
    return public_value

# Client Configuration
SERVER_IP = "192.168.0.182"  # Replace with your server's IP address
PORT = 5000  # Port to connect to the server

# Generate RSA keys for secure DH parameter exchange
private_key, public_key = generate_rsa_keys()

# Connect to the server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1048576)  # Increase buffer size
client.connect((SERVER_IP, PORT))
print(f"Connected to the server at {SERVER_IP}:{PORT}")

try:
    # Key exchange timing
    key_exchange_start = time.time()

    # 1. Exchange RSA Public Keys
    # Receive the server's public key
    server_public_key_bytes = client.recv(4096)
    server_public_key = serialization.load_pem_public_key(server_public_key_bytes)

    # Send the client's public key
    client_public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    client.sendall(client_public_key_bytes)

    # 2. Receive DH Parameters (p, g)
    encrypted_dh_params = client.recv(4096)
    dh_params = rsa_decrypt(private_key, encrypted_dh_params).decode()
    p, g = map(int, dh_params.split(","))
    print(f"Received DH parameters: p={p}, g={g}")

    # Generate client's DH private value and public value
    client_private_value = random.randint(2, p - 2)
    client_dh_public = diffie_hellman(p, g, client_private_value)

    # Encrypt and send the client's DH public value
    encrypted_client_dh_public = rsa_encrypt(server_public_key, str(client_dh_public).encode())
    client.sendall(encrypted_client_dh_public)

    # Receive and decrypt the server's DH public value
    encrypted_server_dh_public = client.recv(4096)
    server_dh_public = int(rsa_decrypt(private_key, encrypted_server_dh_public))

    # Compute the shared secret
    shared_secret = pow(server_dh_public, client_private_value, p)
    aes_key = shared_secret.to_bytes(32, "big")[:32]  # Use first 32 bytes as AES key
    iv = os.urandom(16)

    # Send IV to the server
    client.sendall(iv)

    # Key exchange completed
    key_exchange_time = (time.time() - key_exchange_start) * 1000  # Convert to milliseconds
    print(f"Key Exchange Time: {key_exchange_time:.2f} ms")

    # AES encryption setup
    cipher = create_aes_cipher(aes_key, iv)
    encryptor = cipher.encryptor()

    # 3. Capture and Encrypt Video Frames
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Unable to access the camera.")
        exit()

    frame_count = 0
    start_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame.")
                break

            # Resize the frame
            frame = cv2.resize(frame, (640, 480))

            # Record the start time for encryption
            encryption_start_time = time.time()

            # Encode frame as JPEG with compression
            _, encoded_frame = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 30])
            frame_data = encoded_frame.tobytes()

            # Encrypt the frame
            encrypted_frame = encryptor.update(frame_data)

            # Calculate encryption time
            encryption_time = time.time() - encryption_start_time

            # Send frame length and encrypted frame
            frame_length = len(encrypted_frame)
            client.sendall(struct.pack("!I", frame_length))  # Send frame length
            client.sendall(encrypted_frame)  # Send encrypted frame

            # Calculate FPS
            frame_count += 1
            elapsed_time = time.time() - start_time
            fps = frame_count / elapsed_time

            # Display metrics
            print(f"Encryption Time: {encryption_time:.4f} seconds | Total Frames: {frame_count} | FPS: {fps:.2f}")

            # Limit FPS (e.g., 30 FPS)
            time.sleep(0.033)

            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        cap.release()
        print("Video capture stopped.")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    client.close()
    print("Connection closed.")
