import cv2
import socket
import os
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Setup video capture (USB camera)
cap = cv2.VideoCapture(0)  # Ensure this is the correct index for your USB camera
if not cap.isOpened():
    print("Error: Could not open video capture.")
    exit()

# Set the resolution to a known good value
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


# Setup TCP socket (to send encrypted video)
server_ip = '192.168.50.66'  # Replace with the laptop's IP address
server_port = 5001  # Port to connect to the laptop
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Use TCP socket

# Connect to the laptop
sock.connect((server_ip, server_port))
print(f"Connected to {server_ip}:{server_port}")  # Debug: Connection status

# Setup for encryption (ChaCha20)
key = os.urandom(32)  # 256-bit key
nonce = os.urandom(12)  # 96-bit nonce for ChaCha20
nonce = nonce + b'\x00' * (16 - len(nonce))  # Pad to 16 bytes (128 bits)
print(f"Sent nonce: {nonce.hex()}")  # Debug: Print nonce before sending

cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())

# Function to encrypt and send video frame in chunks
def encrypt_and_send_frame(frame):
    # Convert frame to bytes (JPEG encoding)
    frame_data = cv2.imencode('.jpg', frame)[1].tobytes()

    # Encrypt the data using the ChaCha20 cipher
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(frame_data)

    # Send the nonce first (needed for decryption)
    sock.send(nonce)  # Send nonce first
    print(f"Sent encrypted data, size: {len(encrypted_data)} bytes")  # Debug: Data size

    # Send the encrypted data in one go (for simplicity)
    sock.send(encrypted_data)

# Loop to capture and send video frames
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break
   # if ret:
     #   cv2.imshow("test frame", frame)
        #cv2.waitkey(0)
    encrypt_and_send_frame(frame)

cap.release()
sock.close()
