import cv2
import socket
import pickle
import numpy as np
from os import urandom
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

client_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
client_public_key = client_key.public_key()
client_public_key_bytes = client_public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

host, port = "192.168.1.133", 5000
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((host, port))
server_public_key = serialization.load_pem_public_key(client_socket.recv(4096))
client_socket.sendall(client_public_key_bytes)

client_random_value = urandom(32)
encrypted_client_random = server_public_key.encrypt(
    client_random_value,
    OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)
client_socket.sendall(encrypted_client_random)

server_random_value = client_key.decrypt(
    client_socket.recv(256),
    OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)

shared_secret = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b'shared secret'
).derive(client_random_value + server_random_value)

iv = client_socket.recv(16)
cipher = Cipher(algorithms.AES(shared_secret), modes.CFB(iv))
decryptor = cipher.decryptor()

while True:
    frame_size = int.from_bytes(client_socket.recv(4), 'big')
    if frame_size == 0:
        break

    payload = b""
    while len(payload) < frame_size:
        data = client_socket.recv(frame_size - len(payload))
        if not data:
            client_socket.close()
            exit()
        payload += data

    encrypted_frame = pickle.loads(payload)
    decrypted_frame_data = decryptor.update(encrypted_frame)
    frame = pickle.loads(decrypted_frame_data)

    cv2.imshow("Decrypted Video", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

client_socket.close()
cv2.destroyAllWindows()
