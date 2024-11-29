import cv2
import socket
import pickle
import numpy as np
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from os import urandom
import time
# === Configuration ===
host = "0.0.0.0"  # Listen on all interfaces
port = 5000

# === RSA Key Pair Generation ===
print("[INFO] Generating RSA key pair...")
client_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
client_public_key = client_key.public_key()
client_public_key_bytes = client_public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# === Set Up Server Socket ===
print(f"[INFO] Setting up server socket on {host}:{port}...")
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(1)
print("[INFO] Waiting for Raspberry Pi to connect...")
conn, addr = server_socket.accept()
print(f"[SUCCESS] Connected to Raspberry Pi at {addr}")

try:
    # === Key Exchange ===
    # Receive public key from Raspberry Pi
    print("[INFO] Receiving public key from Raspberry Pi...")
    raspberry_public_key_bytes = conn.recv(4096)
    raspberry_public_key = serialization.load_pem_public_key(raspberry_public_key_bytes)
    print("[SUCCESS] Received public key from Raspberry Pi.")

    # Send public key to Raspberry Pi
    print("[INFO] Sending public key to Raspberry Pi...")
    conn.sendall(client_public_key_bytes)

    # Perform Diffie-Hellman exchange
    print("[INFO] Starting Diffie-Hellman key exchange...")
    laptop_random_value = urandom(32)
    encrypted_laptop_random = raspberry_public_key.encrypt(
        laptop_random_value,
        OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    conn.sendall(encrypted_laptop_random)

    raspberry_random_value = client_key.decrypt(
        conn.recv(256),
        OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )

    # Derive shared secret
    shared_secret = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'shared secret'
    ).derive(laptop_random_value + raspberry_random_value)
    print("[SUCCESS] Shared secret derived.")

    # === IV Reception ===
    print("[INFO] Receiving IV for AES encryption...")
    iv = conn.recv(16)
    print(f"[DEBUG] Received IV: {iv.hex()}")

    # Initialize AES decryptor
    cipher = Cipher(algorithms.AES(shared_secret), modes.CFB(iv))
    decryptor = cipher.decryptor()
    print("[INFO] AES decryption initialized.")

    # === Start Receiving Encrypted Video Frames ===
    print("[INFO] Starting video reception...")
    frame_count = 0
    total_bandwidth = 0
    start_stream_time = time.time()

    while True:
        # Receive frame size
        frame_size_data = conn.recv(4)
        if not frame_size_data:
            print("[INFO] No more data received. Stopping...")
            break
        frame_size = int.from_bytes(frame_size_data, 'big')

        # Receive the payload
        payload = b""
        while len(payload) < frame_size:
            data = conn.recv(frame_size - len(payload))
            if not data:
                print("[ERROR] Connection closed unexpectedly.")
                conn.close()
                exit()
            payload += data

        # Deserialize encrypted frame
        encrypted_frame = pickle.loads(payload)

        # Decrypt the frame data
        decrypted_frame_data = decryptor.update(encrypted_frame)

        # Deserialize the decrypted frame
        frame = pickle.loads(decrypted_frame_data)

        # Display the frame
        cv2.imshow("Decrypted Video", frame)
        frame_count += 1
        total_bandwidth += frame_size
        print(f"[DEBUG] Received and displayed frame {frame_count}, size: {frame_size} bytes")

        # Exit if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[INFO] 'q' pressed. Exiting video stream.")
            break

    # === Cleanup ===
    end_stream_time = time.time()
    total_stream_time = end_stream_time - start_stream_time

    print("[INFO] Video reception ended.")
    print(f"[INFO] Total frames received: {frame_count}")
    print(f"[INFO] Total bandwidth used: {total_bandwidth / 1_000_000:.2f} MB")
    print(f"[INFO] Average bandwidth: {total_bandwidth / total_stream_time / 1_000:.2f} KB/s")

except Exception as e:
    print(f"[ERROR] An error occurred: {e}")

finally:
    conn.close()
    server_socket.close()
    cv2.destroyAllWindows()
    print("[INFO] Server socket closed.")

