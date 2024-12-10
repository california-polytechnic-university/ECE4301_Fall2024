import cv2
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Util.Padding import pad
import socket
import time
import numpy as np

def encrypt_frame(frame, aes_cipher):
    return aes_cipher.encrypt(pad(frame.tobytes(), AES.block_size))

if __name__ == "__main__":
    HOST = '192.168.0.12'
    PORT = 8080
    SHARED_KEY = b'123456790abcdef' # Replace with actual shared key
    SHARED_KEY = get_random_bytes(16)

    # Define IV
    IV = b'0' * 16

print(f"Key length: {len(SHARED_KEY)} bytes")
if len(SHARED_KEY) not in [16, 24, 32]:
    raise ValueError("Incorrect AES key length. Must be 16, 24, or 32 bytes.")


    aes_cipher = AES.new(SHARED_KEY, AES.MODE_CBC, iv=IV)
    cap = cv2.VideoCapture(0)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            encrypted_frame = encrypt_frame(frame, aes_cipher)
            s.sendall(encrypted_frame)
            time.sleep(0.033)  # 30 FPS
