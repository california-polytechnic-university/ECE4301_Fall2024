import socket
import pickle
from Crypto.Cipher import ChaCha20
import numpy as np
import cv2

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.bind(('172.20.10.2', 9999))  

print("Waiting for encryption key...")
key, _ = client_socket.recvfrom(65536)
print("Encryption key received.")

print("Waiting for encrypted video stream...")
frame_chunks = {}

while True:
    data, _ = client_socket.recvfrom(65536)
    
    nonce, chunk, is_first = pickle.loads(data)

    if is_first:
        frame_chunks[nonce] = chunk
    else:
        frame_chunks[nonce] += chunk

    if nonce in frame_chunks:
        cipher = ChaCha20.new(key=key, nonce=nonce)
        decrypted_frame_bytes = cipher.decrypt(frame_chunks.pop(nonce))

        decrypted_frame_array = np.frombuffer(decrypted_frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(decrypted_frame_array, cv2.IMREAD_COLOR)

        if frame is not None:
            cv2.imshow('Decrypted Video Stream', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

client_socket.close()
cv2.destroyAllWindows()
print("Decryption and display ended.")
