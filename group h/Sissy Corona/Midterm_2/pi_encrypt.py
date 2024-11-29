import time
import cv2
import socket
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.hashes import SHA256
import os

# Generate RSA Key Pair
start_time = time.time()
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
keygen_time = time.time() - start_time

public_key = private_key.public_key()

# Socket Setup
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 5000
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print("Waiting for a connection...")
conn, addr = server_socket.accept()
print(f"Connection from {addr}")

# Send RSA Public Key to Client
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)
conn.sendall(public_pem)

# Receive AES Key from Client
start_time = time.time()
encrypted_aes_key = conn.recv(256)
aes_key = private_key.decrypt(
    encrypted_aes_key,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=SHA256()),
        algorithm=SHA256(),
        label=None
    )
)
key_exchange_time = time.time() - start_time

# AES Encryption Setup
iv = os.urandom(16)
conn.sendall(iv)  # Send IV to Client
cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv))
encryptor = cipher.encryptor()

# Display Timing Information
print(f"RSA Key Generation Time: {keygen_time:.6f} seconds")
print(f"Diffie-Hellman Key Exchange Time: {key_exchange_time:.6f} seconds")

# Start Video Stream
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Original Video Stream",frame)

  # Encode Frame
    _, buffer = cv2.imencode('.jpg', frame)

    # Measure Encryption Time
    start_time = time.time()
    encrypted_frame = encryptor.update(buffer.tobytes())
    encryption_time = time.time() - start_time

    # Send Encrypted Frame
    conn.sendall(len(encrypted_frame).to_bytes(4, 'big') + encrypted_frame)

    print(f"Frame Encryption Time: {encryption_time:.6f} seconds")  # Display encryption time

cap.release()
conn.close()
server_socket.close()
