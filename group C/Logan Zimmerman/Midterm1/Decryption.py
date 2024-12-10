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
    try:
        data, _ = client_socket.recvfrom(65536)
        
        nonce, chunk, is_first = pickle.loads(data)

        if is_first:
            frame_chunks[nonce] = chunk
        else:
            frame_chunks[nonce] += chunk

        if nonce in frame_chunks:
            encrypted_frame = frame_chunks.pop(nonce)

            encrypted_array = np.frombuffer(encrypted_frame[:320 * 240], dtype=np.uint8)
            if encrypted_array.size < 320 * 240:
                encrypted_array = np.pad(
                    encrypted_array, 
                    (0, 320 * 240 - encrypted_array.size), 
                    mode='constant', 
                    constant_values=0
                )
            encrypted_image = encrypted_array.reshape((240, 320))
            encrypted_colored = cv2.applyColorMap(encrypted_image, cv2.COLORMAP_JET)
            cv2.imshow('Encrypted Video Stream (Garbled)', encrypted_colored)

            cipher = ChaCha20.new(key=key, nonce=nonce)
            decrypted_frame_bytes = cipher.decrypt(encrypted_frame)

            decrypted_frame_array = np.frombuffer(decrypted_frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(decrypted_frame_array, cv2.IMREAD_COLOR)

            if frame is not None:
                cv2.imshow('Decrypted Video Stream', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    except Exception as e:
        print(f"Error: {e}")
        break

client_socket.close()
cv2.destroyAllWindows()
print("Decryption and display ended.")

