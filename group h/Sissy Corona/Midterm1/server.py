import socket
import cv2
import numpy as np
from Cryptodome.Cipher import ChaCha20
from Cryptodome.Random import get_random_bytes
import os

cap = cv2.VideoCapture(0)
key = get_random_bytes(32)
nonce = get_random_bytes(12)

cipher = ChaCha20.new(key=key, nonce=nonce)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('192.168.1.142', 5000)

desktop_path = os.path.expanduser("~/Desktop")

ret,frame = cap.read()
if ret:
        before_path = os.path.join(desktop_path, "before_encrpt.jpg")
        cv2.imwrite(before_path, frame)
        print(f"'Before Encrypt' image saved at {before_path}")

print("Streaming video to:",server_address)

while cap.isOpened():
        ret,frame = cap.read()
        if not ret:
                break

        frame = cv2.resize(frame, (640,40))
        _,frame_bytes = cv2.imencode('.jpg',frame)
        frame_data = frame_bytes.tobytes()

encrypted_frame_data = cipher.encrypt(frame_data)

if "after_path" not in locals():
        encrypted_frame = cv2.imdecode(np.frombuffer(enccrypted_frame_data, dtype=np.uint8),1)
        after_path = os.path.join(deskptop_path, "after_encrpt.jpg")
        cv2.imwrite(after_path, encrypted_frame)
        print(f"'After Encryption' image saved at {after_path}")

        server_socket.sendto(encrypted_frame_data,server_address)

cap.release()
server_socket.close()
