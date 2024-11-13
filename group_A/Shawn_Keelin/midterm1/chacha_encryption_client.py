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
        client_socket.connect(('192.168.137.29', 8000))  # Replace 'YOUR_PI_IP' with the IP of your Raspberry Pi
        connected = True
    except socket.error as e:
        print(f"Connection failed: {e}. Retrying in 5 seconds...")
        time.sleep(5)

# Receive the key and nonce from the Raspberry Pi
key = client_socket.recv(32)
nonce = client_socket.recv(12)
print("Received key and nonce from the server...")

# Receive the video frame dimensions (width and height)
frame_width, frame_height = struct.unpack('<II', client_socket.recv(8))
print(f"Received frame dimensions: {frame_width}x{frame_height}")

# Function to display encrypted data as an image (visualization only)
def visualize_encrypted_data(data, width, height):
    # Convert encrypted data into grayscale for visualization
    img_size = min(len(data), width * height)  # Limit size to frame dimensions
    img_array = np.frombuffer(data[:img_size], dtype=np.uint8)
    img_array = np.pad(img_array, (0, width * height - len(img_array)), mode='constant')  # Zero padding
    img_array = img_array.reshape((height, width))
    return img_array

data = b''

while True:
    # Receive the length of the incoming frame
    packed_length = client_socket.recv(4)
    if not packed_length:
        break
    frame_length = struct.unpack('<L', packed_length)[0]

    # Receive the encrypted frame
    while len(data) < frame_length:
        data += client_socket.recv(frame_length - len(data))

    encrypted_frame = data[:frame_length]
    data = data[frame_length:]

    # Visualize encrypted data (optional)
    encrypted_visualization = visualize_encrypted_data(encrypted_frame, frame_width, frame_height)

    # Decrypt the frame using ChaCha20
    cipher = ChaCha20.new(key=key, nonce=nonce)
    decrypted_frame = cipher.decrypt(encrypted_frame)

    # Decode the decrypted frame from JPEG
    frame = np.frombuffer(decrypted_frame, dtype=np.uint8)
    decoded_frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

    # Display the frames
    cv2.imshow('Encrypted Data (Visualization)', encrypted_visualization)
    cv2.imshow('Decrypted Frame', decoded_frame)

    # Exit on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

client_socket.close()
cv2.destroyAllWindows()