import socket
import cv2
import numpy as np
from Cryptodome.Cipher import ChaCha20
from Cryptodome.Random import get_random_bytes
import os
import time

# Generate key and nonce
key = get_random_bytes(32)  # 32 bytes = 256-bit key
nonce = get_random_bytes(12)  # Recommended size for ChaCha20 nonce

# Save key and nonce to a text file with a timestamp
from datetime import datetime
key_nonce_file = os.path.expanduser(f"~/Desktop/key_nonce.txt")
with open(key_nonce_file, 'w') as f:
    f.write(f"Key: {key.hex()}\n")
    f.write(f"Nonce: {nonce.hex()}\n")
print(f"Key and Nonce saved to: {key_nonce_file}")

# Set up the cipher for encryption
cipher = ChaCha20.new(key=key, nonce=nonce)

# Set up video capture and TCP socket
cap = cv2.VideoCapture(0)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('192.168.1.131', 5000)
server_socket.bind(server_address)
server_socket.listen(1)  # Listen for a single connection

print("Waiting for connection...")
connection, client_address = server_socket.accept()  # Accept the connection
print(f"Connection established with {client_address}")
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Resize and encode the frame
    frame = cv2.resize(frame, (320,240))
    _, frame_bytes = cv2.imencode('.jpg', frame)
    frame_data = frame_bytes.tobytes()
    # Display the original (unencrypted) frame
    cv2.imshow("Original Video Stream", frame)

    # Measure encryption time
    start_time = time.time()
    encrypted_frame_data = cipher.encrypt(frame_data)
    encryption_time = time.time() - start_time
    print(f"Frame encrypted in {encryption_time:.6f} seconds")

    frame_length = len(encrypted_frame_data)
    print(f"Sending frame of length; {frame_length} bytes")

    # Send encrypted frame over TCP
    connection.sendall(encrypted_frame_data)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources and close windows
cap.release()
connection.close()
server_socket.close()
cv2.destroyAllWindows()
