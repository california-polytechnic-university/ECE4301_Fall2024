import socket
import pickle
import time
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from os import urandom  
import cv2

private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()
public_key_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('172.20.10.2', 5001))
server_socket.listen(1)
print("Listening for connection...")

client_socket, addr = server_socket.accept()
print(f"Connection established with {addr}")

start_key_exchange = time.time()

try:
    client_socket.sendall(public_key_bytes)
    pi_public_key_bytes = client_socket.recv(4096)
    pi_public_key = serialization.load_pem_public_key(pi_public_key_bytes)

    laptop_random_value = urandom(32)
    encrypted_random_value = pi_public_key.encrypt(
        laptop_random_value,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    client_socket.sendall(encrypted_random_value)

    pi_encrypted_value = client_socket.recv(256)
    pi_random_value = private_key.decrypt(
        pi_encrypted_value,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
except Exception as e:
    print(f"[ERROR] Key exchange failed: {e}")
    client_socket.close()
    server_socket.close()
    exit()

shared_secret = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b'shared secret'
).derive(pi_random_value + laptop_random_value)

end_key_exchange = time.time()
key_exchange_time = end_key_exchange - start_key_exchange
print(f"[SUCCESS] Shared secret derived in {key_exchange_time:.2f} seconds.")

iv = client_socket.recv(16)
cipher = Cipher(algorithms.AES(shared_secret), modes.CFB(iv))
decryptor = cipher.decryptor()

print("[INFO] Receiving video stream...")

start_stream = time.time()
frame_count = 0
total_bytes_received = 0

try:
    while True:
        frame_length_bytes = client_socket.recv(4)
        if not frame_length_bytes:
            break
        frame_length = int.from_bytes(frame_length_bytes, 'big')

        frame_start = time.time()
        frame_data = b''
        while len(frame_data) < frame_length:
            packet = client_socket.recv(frame_length - len(frame_data))
            if not packet:
                raise ConnectionResetError
            frame_data += packet

        decrypted_frame = decryptor.update(frame_data)
        frame = pickle.loads(decrypted_frame)

        decryption_time = time.time() - frame_start
        frame_count += 1
        total_bytes_received += frame_length
        elapsed_time = time.time() - start_stream
        fps = frame_count / elapsed_time
        bandwidth = total_bytes_received / elapsed_time

        print(f"[INFO] Decryption Time: {decryption_time:.4f}s | FPS: {fps:.2f} | Bandwidth: {bandwidth:.2f} B/s")

        cv2.imshow('Video Stream', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except (ConnectionResetError, BrokenPipeError):
    print("[ERROR] Connection to Raspberry Pi lost.")
finally:
    client_socket.close()
    server_socket.close()
    cv2.destroyAllWindows()
    print("[INFO] Connection closed.")
