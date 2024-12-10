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
from cryptography.hazmat.primitives.serialization import load_pem_public_key

private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

public_key_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 5000))
server_socket.listen(1)
print("Listening for connection...")

client_socket, addr = server_socket.accept()
print(f"Connection established with {addr}")

client_socket.sendall(public_key_bytes)

raspberry_public_key_bytes = client_socket.recv(4096)
raspberry_public_key = load_pem_public_key(raspberry_public_key_bytes)

laptop_random_value = urandom(32)
encrypted_random_value = raspberry_public_key.encrypt(
    laptop_random_value,
    OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)
client_socket.sendall(encrypted_random_value)

raspberry_encrypted_value = client_socket.recv(256)
raspberry_random_value = private_key.decrypt(
    raspberry_encrypted_value,
    OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)

shared_secret = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b'shared secret'
).derive(laptop_random_value + raspberry_random_value)

print("[SUCCESS] Shared secret derived.")

iv = client_socket.recv(16)
cipher = Cipher(algorithms.AES(shared_secret), modes.CFB(iv))
decryptor = cipher.decryptor()

cv2.namedWindow("Decrypted Video", cv2.WINDOW_NORMAL)

while True:
    frame_length_data = client_socket.recv(4)
    if not frame_length_data:
        print("[INFO] No more data received. Exiting...")
        break

    frame_length = int.from_bytes(frame_length_data, 'big')

    encrypted_frame_data = b""
    while len(encrypted_frame_data) < frame_length:
        packet = client_socket.recv(frame_length - len(encrypted_frame_data))
        if not packet:
            print("[ERROR] Connection lost while receiving frame.")
            break
        encrypted_frame_data += packet

    decrypted_frame_data = decryptor.update(encrypted_frame_data)

    frame = pickle.loads(decrypted_frame_data)
    cv2.imshow("Decrypted Video", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("[INFO] 'q' pressed. Exiting...")
        break

# Cleanup
client_socket.close()
server_socket.close()
cv2.destroyAllWindows()
print("[INFO] Connection closed.")
