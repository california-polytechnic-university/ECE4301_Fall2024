import socket, cv2, time, numpy as np
from Crypto.Cipher import ChaCha20_Poly1305
import win_config  # Import the configuration file

# Function to decrypt data using ChaCha20-Poly1305
def decrypt_chacha20(key, nonce, data, tag):
    cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    return cipher.decrypt_and_verify(data, tag)

# Set up the socket server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((win_config.HOST, win_config.PORT))  # Use variables from win_config
server_socket.listen(1)

print("Waiting for connection...")
conn, addr = server_socket.accept()
print(f"Connected by {addr}")

# Receive the key and nonce
key = conn.recv(32)  # Assuming the key is 32 bytes
nonce = conn.recv(12)  # Assuming the nonce is 12 bytes

try:
    while True:
        data = b''
        while len(data) < 4096 + 16:  # Adjust the size as needed
            packet = conn.recv(4096 + 16 - len(data))
            if not packet:
                break
            data += packet

        if not data:
            break

        # Assuming the last 16 bytes are the tag
        tag = data[-16:]
        encrypted_data = data[:-16]

        # Display the raw encrypted data with a caption
        encrypted_frame = np.frombuffer(encrypted_data, dtype=np.uint8).reshape((480, 640, 3))  # Adjust the shape as needed
        cv2.putText(encrypted_frame, 'Raw Encrypted Data', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.imshow('Encrypted Frame', encrypted_frame)

        # Measure the time taken to decrypt the data
        start_time = time.time()
        decrypted_data = decrypt_chacha20(key, nonce, encrypted_data, tag)
        end_time = time.time()
        decryption_time = end_time - start_time

        # Convert the decrypted data to a numpy array and reshape it to the original frame size
        frame = np.frombuffer(decrypted_data, dtype=np.uint8).reshape((480, 640, 3))  # Adjust the shape as needed

        # Add a caption to the decrypted frame indicating it is decrypted and the decryption time
        caption = f'Decrypted Data - Time: {decryption_time:.4f}s'
        cv2.putText(frame, caption, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        # Display the decrypted frame with the caption
        cv2.imshow('Decrypted Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    conn.close()
    server_socket.close()
    cv2.destroyAllWindows()
