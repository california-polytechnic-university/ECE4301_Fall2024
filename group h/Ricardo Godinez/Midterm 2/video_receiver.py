import cv2
import numpy as np
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import unpad
import socket

def decrypt_frame(encrypted_frame, aes_cipher, frame_shape):
    decrypted_data = unpad(aes_cipher.decrypt(encrypted_frame), AES.block_size)
    return np.frombuffer(decrypted_data, dtype=np.uint8).reshape(frame_shape)

if __name__ == "__main__":
    HOST = '192.168.0.12'
    PORT = 8080
    SHARED_KEY = b'1234567890abcdef'  
    # hard code shared key
    print(f"Key length: {len(SHARED_KEY)} bytes")

    # generate key
    SHARED_KEY = get_random_bytes(16)  # For a 128-bit key

    print(f"Key length: {len(SHARED_KEY)} bytes")
    if len(SHARED_KEY) not in [16, 24, 32]:
        raise ValueError("Incorrect AES key length. Must be 16, 24, or 32 bytes.")\
        
    # Define the IV (must be 16 bytes)
    IV = b'0' * 16  

    # Create AES cipher
    aes_cipher = AES.new(SHARED_KEY, AES.MODE_CBC, iv=IV)
    frame_shape = (480, 640, 3)  # Adjust based on your camera's resolution
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        with conn:
            while True:
                encrypted_frame = conn.recv(921600)  # Adjust based on frame size
                frame = decrypt_frame(encrypted_frame, aes_cipher, frame_shape)
                cv2.imshow('Video', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    cv2.destroyAllWindows()
