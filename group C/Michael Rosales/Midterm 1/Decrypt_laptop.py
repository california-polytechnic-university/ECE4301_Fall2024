import socket
import cv2
import numpy as np
import time
from Crypto.Cipher import ChaCha20

# Frame dimensions (match these to the size used in encryption)
frame_height = 480
frame_width = 640
frame_size = frame_height * frame_width * 3  # For an RGB image, 3 bytes per pixel

# Setup socket to receive frames
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('0.0.0.0', 9999))
sock.listen(1)
conn, addr = sock.accept()

# Use fixed key and nonce (same as used on the Raspberry Pi)
key = b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20'  # 32-byte key
nonce = b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c'  # 12-byte nonce

def receive_full_frame(conn, frame_size):
    data = b''
    while len(data) < frame_size:
        packet = conn.recv(frame_size - len(data))  # Receive chunk by chunk
        if not packet:
            break
        data += packet
    return data

while True:
    # Receive the full encrypted frame
    encrypted_frame = receive_full_frame(conn, frame_size)
    
    if len(encrypted_frame) != frame_size:
        print("Incomplete frame received, skipping...")
        continue
    
    # Measure decryption time
    start_time = time.time()

    # Reinitialize cipher for each frame with the fixed key and nonce
    cipher = ChaCha20.new(key=key, nonce=nonce)

    # Decrypt the frame
    decrypted_frame = cipher.decrypt(encrypted_frame)
    
    end_time = time.time()
    decryption_time = end_time - start_time
    print(f"Decryption Time: {decryption_time:.6f} seconds")
    
    # Reshape the decrypted frame into an image
    frame = np.frombuffer(decrypted_frame, dtype=np.uint8).reshape((frame_height, frame_width, 3))
    
    # Display the decrypted video stream
    cv2.imshow('Decrypted Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

conn.close()
cv2.destroyAllWindows()
