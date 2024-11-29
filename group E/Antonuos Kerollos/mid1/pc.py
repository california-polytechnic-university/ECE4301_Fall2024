import cv2
import socket
import struct
import numpy as np
from Crypto.Cipher import ChaCha20
import time

# Set up socket for receiving video
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Attempt to connect and retry if failed
connected = False
while not connected:
    try:
        client_socket.connect(('192.168.1.99', 8000))  
        connected = True
    except socket.error as e:
        print(f"Connection failed: {e}. Retrying in 5 seconds...")
        time.sleep(5)

# Receive the key and nonce from the Raspberry Pi
key = client_socket.recv(32)
nonce = client_socket.recv(12)
print("Received key and nonce from the server...")

# Receive the video frame dimensions (width and height)
frame_width, frame_height = struct.unpack('<LL', client_socket.recv(8))
print(f"Received frame dimensions: {frame_width}x{frame_height}")

while True:
    # Receive the length of the incoming frame
    packed_length = client_socket.recv(4)
    if not packed_length:
        break
    frame_length = struct.unpack('<L', packed_length)[0]

    # Receive the encrypted frame
    encrypted_frame = b''
    while len(encrypted_frame) < frame_length:
        encrypted_frame += client_socket.recv(frame_length - len(encrypted_frame))

    # Decrypt the frame
    cipher = ChaCha20.new(key=key, nonce=nonce)
    frame_data = cipher.decrypt(encrypted_frame)

    # Convert the frame data to an image
    frame = np.frombuffer(frame_data, dtype=np.uint8).reshape((frame_height, frame_width, 3))

    # Display the frame
    cv2.imshow('Video', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

client_socket.close()
cv2.destroyAllWindows()
