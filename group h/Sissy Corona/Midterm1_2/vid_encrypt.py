import cv2
import socket
import ssl
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import pickle

# Generate ChaCha20 key and nonce
key = os.urandom(32)
nonce = os.urandom(16)

# Socket setup
HOST = '192.168.1.142'  # Replace with the laptop's IP
PORT = 9999

# Create a regular socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Wrap the socket with TLS
tls_socket = ssl.wrap_socket(sock, keyfile=None, certfile=None, server_side=False)

# Connect to the laptop (TLS connection)
tls_socket.connect((HOST, PORT))

# Send key and nonce securely via TLS
metadata = pickle.dumps({'key': key, 'nonce': nonce})
tls_socket.sendall(metadata)

# Initialize video capture
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if ret:
        # Process the frame (e.g., display it)
        cv2.imshow("Frame", frame)
    else:
        print("Failed to capture frame.")
        break
# Resize frame for faster transmission
    frame = cv2.resize(frame, (640, 480))
    # Serialize frame to bytes
    data = cv2.imencode('.jpg', frame)[1].tobytes()
    # Encrypt frame
    encrypted_data = Cipher.encryptor(data)
    # Encode frame as JPEG
    _, buffer = cv2.imencode('.jpg', frame)
    # Encrypt frame
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_frame = encryptor.update(buffer.tobytes())
    # Send frame size and encrypted frame securely
    tls_socket.sendall(len(encrypted_frame).to_bytes(4, 'big'))
    tls_socket.sendall(encrypted_frame)

cap.release()
tls_socket.close()
