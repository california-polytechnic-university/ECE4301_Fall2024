import cv2
import socket
import os
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.backends import default_backend
import struct

# Function to apply ChaCha20 encryption
def encrypt_frame(key, nonce, frame):
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_frame = encryptor.update(frame.tobytes()) + encryptor.finalize()
    return encrypted_frame

# Initialize socket connection (Raspberry Pi acting as the client)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.1.133', 1900))  # Replace with your PC's IP address

# Create folder to store encrypted frames (optional)
folder_name = "ChaChaCipher_Frame"
if not os.path.exists(folder_name):
    os.makedirs(folder_name)
    print(f"Folder '{folder_name}' created")

# ChaCha20 key (32 bytes)
key = b'This_is_a_32_byte_long_key!!_abc'

# Open the webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

frame_counter = 0
total_encryption_time = 0
total_transmission_time = 0
total_execution_time = 0  # Ensure this is initialized
start_time = time.time()  # Start overall time for FPS calculation

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame.")
            break

        # Display the original frame (for feedback on Raspberry Pi)
        cv2.imshow("Original Video Before Encryption (Raspberry Pi)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Generate a new nonce (16 bytes) for each frame
       nonce = os.urandom(16)

        # Start execution timer
        exec_start_time = time.time()  # Initialize here for each loop iteration

        # Encrypt the frame
        enc_start_time = time.time()
        encrypted_frame = encrypt_frame(key, nonce, frame)
        enc_end_time = time.time()

        encryption_time = enc_end_time - enc_start_time
        total_encryption_time += encryption_time
        print(f"Frame {frame_counter} encryption time: {encryption_time:.6f} seconds")

        # Start transmission timer
        trans_start_time = time.time()

        # Send nonce (16 bytes)
        client_socket.sendall(nonce)

        # Send frame shape (height, width, channels)
        frame_shape = frame.shape
        client_socket.sendall(struct.pack("3I", *frame_shape))
 # Send length of encrypted frame
        client_socket.sendall(struct.pack("Q", len(encrypted_frame)))

        # Send encrypted frame
        client_socket.sendall(encrypted_frame)

        trans_end_time = time.time()
        transmission_time = trans_end_time - trans_start_time
        total_transmission_time += transmission_time
        print(f"Frame {frame_counter} transmission time: {transmission_time:.6f} seconds")

        # Save encrypted frame to a file (optional for verification)
        frame_filename = os.path.join(folder_name, f'encrypted_frame_{frame_counter}.bin')
        with open(frame_filename, 'wb') as f:
            f.write(encrypted_frame)

        print(f"Frame {frame_counter} captured, encrypted, and saved as {frame_filename}")

        # Calculate and update total execution time
        exec_end_time = time.time()
        execution_time = exec_end_time - exec_start_time
        total_execution_time += execution_time

        frame_counter += 1

        # Calculate and display FPS every 10 frames
        if frame_counter % 10 == 0:
            elapsed_time = time.time() - start_time
            fps = frame_counter / elapsed_time
            avg_encryption_time = total_encryption_time / frame_counter
            avg_transmission_time = total_transmission_time / frame_counter
            avg_execution_time = total_execution_time / frame_counter  # Average execution time
            print(f"FPS (after {frame_counter} frames): {fps:.2f}")
            print(f"Average Encryption Time: {avg_encryption_time:.6f} seconds")
            print(f"Average Transmission Time: {avg_transmission_time:.6f} seconds")
            print(f"Average Execution Time: {avg_execution_time:.6f} seconds")  # Display average execution time

except KeyboardInterrupt:
    print("Streaming interrupted.")

finally:
    cap.release()
    client_socket.close()
    cv2.destroyAllWindows()
    print("Streaming stopped.")
