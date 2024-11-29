import cv2
import socket
import struct
import pickle
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import hashlib
import os
import time

def calculate_checksum(data):
    """Calculate the SHA-256 checksum of the given data."""
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()

def start_video_stream_server():
    print("Starting server...")

    # Encryption setup using ChaCha20
    key = os.urandom(32)  # 256-bit key
    nonce = os.urandom(16)  # 128-bit nonce (required size for ChaCha20)
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
    encryptor = cipher.encryptor()

    # Open the camera with 640x480 resolution
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("Error: Camera could not be opened.")
        return
    else:
        print("Camera opened successfully.")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 8080))
    server_socket.listen(1)
    print("Server is listening on port 8080...")

    conn, addr = server_socket.accept()
    print(f"Connected to {addr}")

    # Send key and nonce to the client (for testing purposes only, do this securely in production)
    conn.sendall(key + nonce)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture video frame.")
                break

            print("Captured a video frame.")

            # Serialize the frame
            data = pickle.dumps(frame)
            original_checksum = calculate_checksum(data)
            print(f"Original checksum: {original_checksum}")

            # Measure encryption time
            start_time = time.time()
            encrypted_data = encryptor.update(data)
            encryption_time = time.time() - start_time
            encrypted_checksum = calculate_checksum(encrypted_data)
            print(f"Encryption time: {encryption_time:.6f} seconds")
            print(f"Encrypted checksum: {encrypted_checksum}")

            data_size = len(encrypted_data)
            print(f"Encrypted frame size: {data_size} bytes")
            # Send the size of the encrypted data first (4 bytes, network byte order)
            conn.sendall(struct.pack("!I", data_size))

            # Send the encrypted frame data in chunks
            for i in range(0, data_size, 4096):
                conn.sendall(encrypted_data[i:i+4096])

            print("Encrypted frame sent in chunks.")

    except Exception as e:
        print(f"Exception occurred: {e}")

    finally:
        cap.release()
        conn.close()
        server_socket.close()
        print("Server shut down.")

if __name__ == "__main__":
    start_video_stream_server()
