import time
import cv2
import socket
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.hashes import SHA256
import os
import numpy as np

# Generate RSA Key Pair
start_time = time.time()
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
keygen_time = time.time() - start_time

public_key = private_key.public_key()

# Connect to Server
HOST = '192.168.1.131'
PORT = 5000
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# Receive Server's RSA Public Key
server_public_key_pem = client_socket.recv(2048)
server_public_key = serialization.load_pem_public_key(server_public_key_pem)

# Generate AES Key and Send to Server
aes_key = os.urandom(32)

# Measure Key Exchange Time
start_time = time.time()
encrypted_aes_key = server_public_key.encrypt(
    aes_key,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=SHA256()),
        algorithm=SHA256(),
        label=None
    )
)
client_socket.sendall(encrypted_aes_key)
key_exchange_time = time.time() - start_time

# AES Decryption Setup
iv = client_socket.recv(16)
cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv))
decryptor = cipher.decryptor()

# Display Timing Information
print(f"RSA Key Generation Time: {keygen_time:.6f} seconds")
print(f"Diffie-Hellman Key Exchange Time: {key_exchange_time:.6f} seconds")

# Start Video Stream
while True:
    length_data = client_socket.recv(4)
    frame_length = int.from_bytes(length_data, 'big')
    encrypted_frame = b''
    while len(encrypted_frame) < frame_length:
        encrypted_frame += client_socket.recv(frame_length - len(encrypted_frame))

    # Measure Decryption Time
    start_time = time.time()
    decrypted_frame = decryptor.update(encrypted_frame)
    decryption_time = time.time() - start_time

    # Decode Frame and Display
    frame = cv2.imdecode(np.frombuffer(decrypted_frame, np.uint8), cv2.IMREAD_COLOR)
    cv2.imshow("Decrypted Video", frame)
    print(f"Frame Decryption Time: {decryption_time:.6f} seconds")  # Display decryption time

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

client_socket.close()
cv2.destroyAllWindows()
