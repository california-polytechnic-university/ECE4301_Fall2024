import cv2
import socket
import os
import time  # For measuring time
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
client_socket.connect(('192.168.0.23', 8080))  # Replace with the PC's IP address

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
start_time = time.time()  # Start overall time for FPS calculation

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Display the original frame (on Raspberry Pi)
        cv2.imshow("Original Video (Raspberry Pi)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        # Generate a new nonce (16 bytes) for each frame
        nonce = os.urandom(16)

        # Measure encryption time
        enc_start_time = time.time()
        encrypted_frame = encrypt_frame(key, nonce, frame)
        enc_end_time = time.time()

        encryption_time = enc_end_time - enc_start_time
        total_encryption_time += encryption_time
        print(f"Frame {frame_counter} encryption time: {encryption_time:.6f} seconds")
        
        # Measure transmission time
        trans_start_time = time.time()
        
        # Send the nonce (16 bytes)
        client_socket.sendall(nonce)

        # Send the shape of the frame first (height, width, channels)
        frame_shape = frame.shape
        client_socket.sendall(struct.pack("3I", *frame_shape))

        # Send the length of the encrypted frame
        client_socket.sendall(struct.pack("Q", len(encrypted_frame)))

        # Send the encrypted frame in chunks to avoid exceeding buffer size
        client_socket.sendall(encrypted_frame)
        
        trans_end_time = time.time()

        transmission_time = trans_end_time - trans_start_time
        total_transmission_time += transmission_time
        print(f"Frame {frame_counter} transmission time: {transmission_time:.6f} seconds")
        
        # Save encrypted frame to a file (optional, can be used for video saving)
        frame_filename = os.path.join(folder_name, f'encrypted_frame_{frame_counter}.bin')
        with open(frame_filename, 'wb') as f:
            f.write(encrypted_frame)

        print(f"Frame {frame_counter} captured, encrypted, and saved as {frame_filename}")
        
        frame_counter += 1

        # Calculate and display FPS after every 10 frames
        if frame_counter % 10 == 0:
            elapsed_time = time.time() - start_time
            fps = frame_counter / elapsed_time
            print(f"FPS (after {frame_counter} frames): {fps:.2f}")
        
        # Break the loop if frame limit is reached (optional)
        if frame_counter == 100:  # Capture only 100 frames for this example
            frame_counter = 0

except KeyboardInterrupt:
    print("Streaming interrupted.")

finally:
    cap.release()
    client_socket.close()
    cv2.destroyAllWindows()  # Close the window showing the original video
