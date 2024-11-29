import socket, cv2, time, numpy as np
from Crypto.Cipher import ChaCha20_Poly1305
import win_config  # Import the configuration file

# Function to decrypt data using ChaCha20-Poly1305
def decrypt_chacha20(key, nonce, data, tag):
    cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    return cipher.decrypt_and_verify(data, tag)

# Set up the socket server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((win_config.HOST, win_config.PORT))
server_socket.listen(1)

print("Waiting for connection...")
conn, addr = server_socket.accept()
print(f"Connected by {addr}")

# Receive the key and nonce
key = conn.recv(32)
nonce = conn.recv(12)

# Uncomment the next line to simulate using the wrong key
key = b'wrong_key_32_byte_length______'  # Example wrong key with exactly 32 bytes

frame_size = 480 * 640 * 3
expected_size = frame_size + 16

# Variables to track average decryption time
total_decryption_time = 0
frame_count = 0

# Define font outside of try-except block
font = cv2.FONT_HERSHEY_SIMPLEX

try:
    while True:
        data = b''
        while len(data) < expected_size:
            packet = conn.recv(expected_size - len(data))
            if not packet:
                break
            data += packet

        if len(data) < expected_size:
            print("Incomplete data received, skipping this frame.")
            continue

        tag = data[-16:]
        encrypted_data = data[:-16]

        # Attempt decryption and record time
        try:
            start_time = time.time()
            decrypted_data = decrypt_chacha20(key, nonce, encrypted_data, tag)
            decryption_time = time.time() - start_time

            # Update decryption time metrics
            total_decryption_time += decryption_time
            frame_count += 1
            avg_decryption_time = total_decryption_time / frame_count

            # Display the decrypted frame
            frame = np.frombuffer(decrypted_data, dtype=np.uint8).reshape((480, 640, 3))

            # Show metrics window with improved styling
            metrics_frame = np.zeros((200, 400, 3), dtype=np.uint8)
            cv2.putText(metrics_frame, f'Decryption Time: {decryption_time:.4f}s', (20, 60),
                        font, 0.9, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(metrics_frame, f'Avg Decrypt Time: {avg_decryption_time:.4f}s', (20, 120),
                        font, 0.9, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(metrics_frame, 'Decryption Status: Success', (20, 180),
                        font, 0.9, (0, 255, 0), 2, cv2.LINE_AA)

            cv2.imshow('Decrypted Frame', frame)
            cv2.imshow('Receiver Metrics', metrics_frame)

        except ValueError:
            # Handle decryption failure and show error status
            corrupted_data = encrypted_data[:frame_size]
            corrupted_frame = np.frombuffer(corrupted_data, dtype=np.uint8, count=frame_size).reshape((480, 640, 3))

            # Display failure status in metrics window
            metrics_frame = np.zeros((200, 400, 3), dtype=np.uint8)
            cv2.putText(metrics_frame, 'Decryption Time: N/A', (20, 60),
                        font, 0.9, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.putText(metrics_frame, 'Avg Decrypt Time: N/A', (20, 120),
                        font, 0.9, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.putText(metrics_frame, 'Decryption Status: Failed', (20, 180),
                        font, 0.9, (0, 0, 255), 2, cv2.LINE_AA)

            cv2.imshow('Decrypted Frame', corrupted_frame)
            cv2.imshow('Receiver Metrics', metrics_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    conn.close()
    server_socket.close()
    cv2.destroyAllWindows()
