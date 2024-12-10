import socket
import time
import pickle
from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes
from picamera2 import Picamera2
import cv2


key = get_random_bytes(32)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('172.20.10.2', 9999)  

print("Sending encryption key to client...")
server_socket.sendto(key, server_address)

picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (320, 240)})
picam2.configure(config)
picam2.start()
time.sleep(1)  

print("Starting encryption and streaming...")
try:
    while True:
        frame = picam2.capture_array()

        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        frame_bytes = buffer.tobytes()

        nonce = get_random_bytes(12)  
        cipher = ChaCha20.new(key=key, nonce=nonce)
        encrypted_frame = cipher.encrypt(frame_bytes)

        print(f"Original frame size: {len(frame_bytes)}")
        print(f"Encrypted frame size: {len(encrypted_frame)}")

        for i in range(0, len(encrypted_frame), 65000):
            chunk = encrypted_frame[i:i + 65000]
            data = pickle.dumps((nonce, chunk, i == 0)) 
            server_socket.sendto(data, server_address)

except KeyboardInterrupt:
    print("Streaming interrupted.")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    picam2.stop()
    server_socket.close()
    print("Video streaming ended.")
