import socket
import cv2
import pickle
import numpy as np
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from os import urandom


private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

# Export public key for exchange
public_key_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

#connection
laptop_ip = "172.20.10.2"
port = 5000
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((laptop_ip, port))

# exchange keys
client_socket.sendall(public_key_bytes)

laptop_public_key_bytes = client_socket.recv(4096)
laptop_public_key = serialization.load_pem_public_key(laptop_public_key_bytes)

# Diffie-Hellman key exchange
raspberry_random_value = urandom(32)
encrypted_random_value = laptop_public_key.encrypt(
    raspberry_random_value,
    OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)
client_socket.sendall(encrypted_random_value)

laptop_random_value = private_key.decrypt(
    client_socket.recv(256),
    OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)

# Derive shared secret
shared_secret = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b'shared secret'
).derive(laptop_random_value + raspberry_random_value)

#AES
iv = urandom(16)
client_socket.sendall(iv)

cipher = Cipher(algorithms.AES(shared_secret), modes.CFB(iv))
encryptor = cipher.encryptor()

video_capture = cv2.VideoCapture(0)
while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    frame_resized = cv2.resize(frame, (640, 480))
    frame_data = pickle.dumps(frame_resized)
    encrypted_frame = encryptor.update(frame_data)

    payload = pickle.dumps(encrypted_frame)
    client_socket.sendall(len(payload).to_bytes(4, 'big') + payload)

# Cleanup
video_capture.release()
client_socket.close()
