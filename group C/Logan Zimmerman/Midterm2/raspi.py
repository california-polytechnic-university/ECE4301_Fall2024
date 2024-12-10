import socket
import cv2
import pickle
import time
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from os import urandom  # FIXED: Import urandom
from picamera2 import Picamera2


private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()
public_key_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)


server_ip = '172.20.10.2'
server_port = 5001

print("Connecting to laptop...")
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect((server_ip, server_port))
    print("Connected to laptop.")
except Exception as e:
    print(f"[ERROR] Connection failed: {e}")
    exit()

start_key_exchange = time.time()

try:
    laptop_public_key_bytes = client_socket.recv(4096)
    laptop_public_key = serialization.load_pem_public_key(laptop_public_key_bytes)
    client_socket.sendall(public_key_bytes)

    pi_random_value = urandom(32)
    encrypted_random_value = laptop_public_key.encrypt(
        pi_random_value,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    client_socket.sendall(encrypted_random_value)

    laptop_encrypted_value = client_socket.recv(256)
    laptop_random_value = private_key.decrypt(
        laptop_encrypted_value,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
except Exception as e:
    print(f"[ERROR] Key exchange failed: {e}")
    client_socket.close()
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

iv = urandom(16)
client_socket.sendall(iv)
cipher = Cipher(algorithms.AES(shared_secret), modes.CFB(iv))
encryptor = cipher.encryptor()

picam2 = Picamera2()
config = picam2.create_preview_configuration({"size": (640, 480)})
picam2.configure(config)
picam2.start()
time.sleep(2)

print("[INFO] Streaming video...")

# Frame Stats
start_stream = time.time()
frame_count = 0
total_bytes_sent = 0

try:
    while True:
        frame_start = time.time()
        frame = picam2.capture_array()
        frame_data = pickle.dumps(frame)
        encrypted_frame = encryptor.update(frame_data)

        frame_length = len(encrypted_frame).to_bytes(4, 'big')
        client_socket.sendall(frame_length + encrypted_frame)

        frame_count += 1
        total_bytes_sent += len(encrypted_frame)
        encryption_time = time.time() - frame_start
        elapsed_time = time.time() - start_stream
        fps = frame_count / elapsed_time
        bandwidth = total_bytes_sent / elapsed_time

        print(f"[INFO] Encryption Time: {encryption_time:.4f}s | FPS: {fps:.2f} | Bandwidth: {bandwidth:.2f} B/s")

        time.sleep(0.03)

except (BrokenPipeError, ConnectionResetError):
    print("[ERROR] Connection lost.")
except KeyboardInterrupt:
    print("[INFO] Stopping video stream...")
finally:
    client_socket.close()
    picam2.stop()
    print("[INFO] Connection closed.")
