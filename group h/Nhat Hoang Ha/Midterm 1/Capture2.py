import socket
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.backends import default_backend
import struct
import time  # Import time module for measuring execution time

# Function to decrypt the ChaCha20 encrypted data
def decrypt_file(key, nonce, encrypted_data):
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
    return decrypted_data

# Initialize socket connection (PC acting as the server)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 1900))  # Bind to all available interfaces
server_socket.listen(1)

conn, addr = server_socket.accept()
print(f"Connected by {addr}")

# Pre-shared key for decryption (should match the key on the Raspberry Pi)
key = b'This_is_a_32_byte_long_key!!_abc'

# Receive the nonce (16 bytes)
nonce = conn.recv(16)
if not nonce:
    print("No nonce received.")
    conn.close()
    server_socket.close()
    exit()

# Receive the length of the encrypted data
encrypted_length_data = conn.recv(8)
if not encrypted_length_data:
    print("No length data received.")
    conn.close()
    server_socket.close()
    exit()
encrypted_length = struct.unpack("Q", encrypted_length_data)[0]

# Receive the encrypted video data
encrypted_data = b''
while len(encrypted_data) < encrypted_length:
    packet = conn.recv(min(4096, encrypted_length - len(encrypted_data)))
    if not packet:
        break
    encrypted_data += packet

# Receive the recorded video duration (sent as float, can modify the client code to send this)
recorded_duration_data = conn.recv(8)  # Assuming the duration is sent as a float
recorded_duration = struct.unpack("d", recorded_duration_data)[0] if recorded_duration_data else 0.0

# Decrypt the video data
start_decryption_time = time.time()  # Start time for decryption
decrypted_data = decrypt_file(key, nonce, encrypted_data)
end_decryption_time = time.time()  # End time for decryption

# Save the decrypted video file
decrypted_filename = 'Decrypted_Video.avi'
with open(decrypted_filename, 'wb') as f:
    f.write(decrypted_data)

print(f"Received and decrypted video. Saved as '{decrypted_filename}'.")
print(f"Decryption time: {end_decryption_time - start_decryption_time:.2f} seconds")

conn.close()
server_socket.close()
