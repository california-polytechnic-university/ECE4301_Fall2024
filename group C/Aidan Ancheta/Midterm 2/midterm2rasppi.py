import cv2
import socket
import pickle
import numpy as np
from os import urandom
import time
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# === Configuration ===
laptop_ip = "192.168.1.100"  # Replace with your laptop's IP address
port = 5000

# === RSA Key Pair Generation ===
print("[INFO] Generating RSA key pair...")
server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
server_public_key = server_key.public_key()
server_public_key_bytes = server_public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# === Connecting to Laptop ===
print(f"[INFO] Connecting to laptop at {laptop_ip}:{port}...")
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect((laptop_ip, port))
    print(f"[SUCCESS] Connected to laptop at {laptop_ip}:{port}")
except Exception as e:
    print(f"[ERROR] Could not connect to laptop: {e}")
    exit()

try:
    # === Key Exchange ===
    # Send public key to laptop
    print("[INFO] Sending public key to laptop...")
    client_socket.sendall(server_public_key_bytes)

    # Receive public key from laptop
    print("[INFO] Receiving public key from laptop...")
    laptop_public_key_bytes = client_socket.recv(4096)
    laptop_public_key = serialization.load_pem_public_key(laptop_public_key_bytes)
    print("[SUCCESS] Received public key from laptop.")

    # Perform Diffie-Hellman exchange
    print("[INFO] Starting Diffie-Hellman key exchange...")
    laptop_random_value = server_key.decrypt(
        client_socket.recv(256),
        OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    raspberry_random_value = urandom(32)
    client_socket.sendall(laptop_public_key.encrypt(
        raspberry_random_value,
        OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    ))

    # Derive shared secret
    shared_secret = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'shared secret'
    ).derive(laptop_random_value + raspberry_random_value)
    print("[SUCCESS] Shared secret derived.")

    # === IV Generation and Sending ===
    print("[INFO] Generating IV for AES encryption...")
    iv = urandom(16)
    print(f"[DEBUG] Generated IV: {iv.hex()}")

    print("[INFO] Sending IV to laptop...")
    client_socket.sendall(iv)
    print("[SUCCESS] IV sent to laptop.")

    # Initialize AES encryptor
    cipher = Cipher(algorithms.AES(shared_secret), modes.CFB(iv))
    encryptor = cipher.encryptor()

    # === Initialize USB Webcam ===
    print("[INFO] Initializing USB webcam...")
    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        raise RuntimeError("[ERROR] Unable to access USB webcam.")

    print("[INFO] Starting video stream...")
    frame_count = 0
    total_bandwidth = 0
    start_stream_time = time.time()

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("[ERROR] Failed to read frame from webcam.")
            break

        # Resize frame and serialize
        frame_resized = cv2.resize(frame, (640, 480))
        frame_data = pickle.dumps(frame_resized)

        # Encrypt frame data
        encrypted_frame = encryptor.update(frame_data)

        # Serialize encrypted frame and calculate size
        payload = pickle.dumps(encrypted_frame)
        frame_size = len(payload)
        total_bandwidth += frame_size

        # Send frame size and encrypted frame
        client_socket.sendall(frame_size.to_bytes(4, 'big') + payload)

        frame_count += 1
        print(f"[DEBUG] Sent frame {frame_count}, size: {frame_size} bytes")

        # Stop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[INFO] 'q' pressed, stopping video stream.")
            break

    # === Cleanup ===
    video_capture.release()
    end_stream_time = time.time()
    total_stream_time = end_stream_time - start_stream_time

    print(f"[INFO] Streaming ended. Total frames sent: {frame_count}")
    print(f"[INFO] Total bandwidth used: {total_bandwidth / 1_000_000:.2f} MB")
    print(f"[INFO] Average bandwidth: {total_bandwidth / total_stream_time / 1_000:.2f} KB/s")

except Exception as e:
    print(f"[ERROR] An error occurred: {e}")

finally:
    # Close socket
    client_socket.close()
    print("[INFO] Connection closed.")
