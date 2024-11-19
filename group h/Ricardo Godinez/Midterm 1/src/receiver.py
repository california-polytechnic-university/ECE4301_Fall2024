import cv2
import socket
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.backends import default_backend
import numpy as np
import struct
import time  # For measuring time

# Function to decrypt ChaCha20 encrypted data
def decrypt_frame(key, nonce, encrypted_frame, shape):
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_bytes = decryptor.update(encrypted_frame) + decryptor.finalize()

    # Convert the decrypted bytes back into an image frame
    decrypted_frame = np.frombuffer(decrypted_bytes, dtype=np.uint8)
    return decrypted_frame.reshape(shape)

def display_hex(data, label):
    hex_output = data.hex()
    print(f"{label} (Hex): {hex_output[:64]}...")  # Print first 64 chars for brevity

# Folder to save decrypted images
decrypted_folder_name = "Decrypted_Images"

if not os.path.exists(decrypted_folder_name):
    os.makedirs(decrypted_folder_name)
    print(f"Folder '{decrypted_folder_name}' created")

# Initialize socket connection (PC acting as the server)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 8080))  # Bind to all available interfaces
server_socket.listen(1)

conn, addr = server_socket.accept()
print(f"Connected by {addr}")

# ChaCha20 key (32 bytes)
key = b'This_is_a_32_byte_long_key!!_abc'

frame_counter = 0
total_decryption_time = 0
total_receive_time = 0

try:
    while True:
        # Measure the time for receiving data
        recv_start_time = time.time()

        # Receive the nonce (16 bytes)
        nonce = conn.recv(16)
        if not nonce:
            break

        # Receive the shape of the frame (height, width, channels)
        frame_shape_data = conn.recv(12)  # 3 integers (4 bytes each)
        if not frame_shape_data:
            break
        frame_shape = struct.unpack("3I", frame_shape_data)

        # Receive the length of the encrypted frame
        encrypted_frame_len_data = conn.recv(8)
        if not encrypted_frame_len_data:
            break
        encrypted_frame_len = struct.unpack("Q", encrypted_frame_len_data)[0]

        # Receive the encrypted frame data
        encrypted_frame = b''
        while len(encrypted_frame) < encrypted_frame_len:
            packet = conn.recv(min(4096, encrypted_frame_len - len(encrypted_frame)))
            if not packet:
                break
            encrypted_frame += packet
        
        recv_end_time = time.time()
        receive_time = recv_end_time - recv_start_time
        total_receive_time += receive_time

        print(f"Frame {frame_counter} data receive time: {receive_time:.6f} seconds")

        # Measure the decryption time
        dec_start_time = time.time()
        decrypted_frame = decrypt_frame(key, nonce, encrypted_frame, frame_shape)
        dec_end_time = time.time()

        decryption_time = dec_end_time - dec_start_time
        total_decryption_time += decryption_time

        print(f"Frame {frame_counter} decryption time: {decryption_time:.6f} seconds")

        # Save the decrypted frame as a jpg image
        decrypted_image_filename = os.path.join(decrypted_folder_name, f'decrypted_frame_{frame_counter}.jpg')
        cv2.imwrite(decrypted_image_filename, decrypted_frame)

        print(f"Decrypted frame saved as {decrypted_image_filename}")

        # Display the decrypted frame
        cv2.imshow('Decrypted Frame', decrypted_frame)
        
        frame_counter += 1
        if frame_counter == 100:
            frame_counter = 0

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("Decryption interrupted.")

finally:
    conn.close()
    server_socket.close()
    cv2.destroyAllWindows()

    # Calculate and display the average times
    avg_decryption_time = total_decryption_time / frame_counter if frame_counter else 0
    avg_receive_time = total_receive_time / frame_counter if frame_counter else 0

    print(f"\n--- Summary ---")
    print(f"Total Frames Processed: {frame_counter}")
    print(f"Average Data Receive Time: {avg_receive_time:.6f} seconds")
    print(f"Average Decryption Time: {avg_decryption_time:.6f} seconds")