import cv2
import numpy as np
import socket
import time
from Crypto.Cipher import ChaCha20

# TCP Socket setup
HOST = '0.0.0.0'
PORT = 12345
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(1)

print("Waiting for connection...")
conn, addr = sock.accept()
print(f"Connected by {addr}")

# Use the same 256-bit key as the Raspberry Pi for decryption
key = b'\x1a\x2b\x3c\x4d\x5e\x6f\x7a\x8b\x9c\xad\xbe\xcf\xda\xeb\xfc\x0d' \
      b'\x1e\x2f\x3a\x4b\x5c\x6d\x7e\x8f\x9a\xab\xbc\xcd\xde\xef\xf0\x11'

# Frame dimensions
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
EXPECTED_FRAME_SIZE = FRAME_WIDTH * FRAME_HEIGHT * 3  # 230400 bytes
DELIMITER = b'\xFF\xFF\xFF\xFF'  # 4-byte delimiter

def read_exact_bytes(conn, num_bytes):
    buffer = b''
    while len(buffer) < num_bytes:
        chunk = conn.recv(num_bytes - len(buffer))
        if not chunk:
            return None
        buffer += chunk
    return buffer

buffer = b''

while True:
    # Measure reception time
    reception_start = time.time()

    # Read bytes until the delimiter is found
    while DELIMITER not in buffer:
        chunk = conn.recv(4096)
        if not chunk:
            print("Connection closed by sender.")
            break
        buffer += chunk

    # Split the buffer at the delimiter
    frame_data, buffer = buffer.split(DELIMITER, 1)

    # Read the 4-byte frame size header from the frame data
    frame_size_bytes = frame_data[:4]
    frame_size = int.from_bytes(frame_size_bytes, byteorder='big')
    print(f"Received frame size: {frame_size}")

    # Ensure the frame size matches expectations
    if frame_size != EXPECTED_FRAME_SIZE:
        print(f"Warning: Unexpected frame size {frame_size}, expected {EXPECTED_FRAME_SIZE}. Skipping frame...")
        continue

    # Extract the encrypted frame and nonce
    encrypted_frame = frame_data[4:4+frame_size]
    nonce = frame_data[4+frame_size:4+frame_size+12]

    reception_end = time.time()

    # Check if the frame data is complete
    if len(encrypted_frame) != EXPECTED_FRAME_SIZE:
        print(f"Incomplete frame received. Expected {EXPECTED_FRAME_SIZE}, got {len(encrypted_frame)}. Skipping frame...")
        continue

    # Measure decryption time
    decryption_start = time.time()
    try:
        cipher = ChaCha20.new(key=key, nonce=nonce)
        decrypted_frame_bytes = cipher.decrypt(encrypted_frame)
    except ValueError as e:
        print(f"Decryption error: {e}")
        continue
    decryption_end = time.time()

    # Ensure the decrypted frame is the correct size
    if len(decrypted_frame_bytes) != EXPECTED_FRAME_SIZE:
        print(f"Unexpected decrypted frame size: {len(decrypted_frame_bytes)}. Skipping frame...")
        continue

    # Convert bytes back into frame format
    decrypted_frame = np.frombuffer(decrypted_frame_bytes, dtype=np.uint8).reshape((FRAME_HEIGHT, FRAME_WIDTH, 3))

    # Measure overall latency
    overall_latency = time.time() - reception_start

    # Display metrics
    print(f"Reception Time: {reception_end - reception_start:.4f} s, "
          f"Decryption Time: {decryption_end - decryption_start:.4f} s, "
          f"Overall Latency: {overall_latency:.4f} s")

    # Display the decrypted video on the laptop
    cv2.imshow('Decrypted Video on Laptop', decrypted_frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cv2.destroyAllWindows()
conn.close()
sock.close()
