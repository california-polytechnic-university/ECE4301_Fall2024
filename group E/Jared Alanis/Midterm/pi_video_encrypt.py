import cv2
import numpy as np
import socket
import time
from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes

# TCP Socket setup
HOST = '192.168.1.207'  # Replace with the laptop's IP address
PORT = 12345
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

# Initialize the camera capture
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# Generate a 256-bit key for ChaCha20 encryption
key = b'\x1a\x2b\x3c\x4d\x5e\x6f\x7a\x8b\x9c\xad\xbe\xcf\xda\xeb\xfc\x0d' \
      b'\x1e\x2f\x3a\x4b\x5c\x6d\x7e\x8f\x9a\xab\xbc\xcd\xde\xef\xf0\x11'

frame_id = 0
EXPECTED_FRAME_SIZE = 320 * 240 * 3  # 230400 bytes
DELIMITER = b'\xFF\xFF\xFF\xFF'  # 4-byte delimiter

while True:
    # Measure frame capture time
    capture_start = time.time()
    ret, frame = cap.read()
    capture_end = time.time()

    if not ret:
        print("Failed to capture video frame.")
        break

    # Measure encryption time
    encryption_start = time.time()
    frame_bytes = frame.tobytes()
    nonce = get_random_bytes(12)
    cipher = ChaCha20.new(key=key, nonce=nonce)
    encrypted_frame = cipher.encrypt(frame_bytes)
    encryption_end = time.time()

    if len(encrypted_frame) != EXPECTED_FRAME_SIZE:
        print(f"Unexpected encrypted frame size: {len(encrypted_frame)}. Skipping frame...")
        continue

    # Prepare frame size header in big-endian format
    frame_size_header = len(encrypted_frame).to_bytes(4, byteorder='big')
    frame_id_bytes = frame_id.to_bytes(4, byteorder='big')
    frame_id = (frame_id + 1) % 256

    # Construct and send the complete packet
    packet = frame_size_header + encrypted_frame + nonce + DELIMITER

    # Measure transmission time
    transmission_start = time.time()
    sock.sendall(packet)
    transmission_end = time.time()

    # Display metrics
    print(f"Capture Time: {capture_end - capture_start:.4f} s, "
          f"Encryption Time: {encryption_end - encryption_start:.4f} s, "
          f"Transmission Time: {transmission_end - transmission_start:.4f} s")

    # Display the original video on the Raspberry Pi
    cv2.imshow('Original Video on Raspberry Pi', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cap.release()
cv2.destroyAllWindows()
sock.close()
