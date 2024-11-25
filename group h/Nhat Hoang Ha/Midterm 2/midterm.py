import cv2
import socket
import pickle
import numpy as np
from os import urandom
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
import time  # For execution timing
import psutil  # For memory and CPU usage monitoring

# RSA Key Generation for the Client
client_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
client_public_key = client_key.public_key()

# Serialize Public Key to Share with the Server
client_public_key_bytes = client_public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Print Client's Public Key
print("\n[Client (Pi)] Public Key:")
print(client_public_key_bytes.decode())
print("[Client (Pi)] Public Key Size:", client_key.key_size, "bits")

# Client Setup
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("192.168.1.213", 8000))  # Replace with your laptop's IP
print("\n[Client (Pi)] Connected to the server!")

# Receive Server's Public Key
server_public_key_bytes = client_socket.recv(4096)
server_public_key = serialization.load_pem_public_key(server_public_key_bytes)

# Display Server's Public Key
print("\n[Server (Laptop)] Public Key:")
print(server_public_key_bytes.decode())
print("[Server (Laptop)] Public Key Size:", server_public_key.key_size, "bits")

# Send Client's Public Key to the Server
client_socket.sendall(client_public_key_bytes)

# Start timing Diffie-Hellman process
start_time = time.time()

# Generate Random Value and Encrypt with Server's Public Key
client_random_value = urandom(32)
encrypted_client_random = server_public_key.encrypt(
    client_random_value,
    OAEP(
        mgf=MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
client_socket.sendall(encrypted_client_random)

# Receive and Decrypt Server's Random Value
encrypted_server_random = client_socket.recv(4096)
server_random_value = client_key.decrypt(
    encrypted_server_random,
    OAEP(
        mgf=MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

# Derive Shared Secret (256-bit key for AES)
shared_secret = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b'shared secret'
).derive(client_random_value + server_random_value)

# End timing and calculate duration
end_time = time.time()
print("\n[Client (Pi)] Shared Key:", shared_secret.hex())
print("[Client (Pi)] Shared Key Size: 256 bits")
print(f"[Client (Pi)] Diffie-Hellman Execution Time: {end_time - start_time:.6f} seconds")

# Video Capture and Encryption
cap = cv2.VideoCapture(0)  # Change to 1 if using a USB camera
if not cap.isOpened():
    print("Error: Unable to access the camera.")
    exit()

frame_count = 0
total_encryption_time = 0

print("\n[Client (Pi)] Starting video capture and encryption...")
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Error: Unable to capture frame from the camera.")
        break

    # Resize the frame to 900x600 for both local display and transmission
    resized_frame = cv2.resize(frame, (900, 600))

    # Display the resized video locally on the Raspberry Pi
    cv2.imshow("Raspberry Pi Video (900x600)", resized_frame)

    # Serialize the frame
    _, frame_buffer = cv2.imencode('.jpg', resized_frame)
    frame_data = frame_buffer.tobytes()

    # Measure the encryption time
    encryption_start_time = time.time()

    # AES Encryption
    iv = urandom(16)
    cipher = Cipher(algorithms.AES(shared_secret), modes.CBC(iv))
    encryptor = cipher.encryptor()
    padder = PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(frame_data) + padder.finalize()
    encrypted_frame = encryptor.update(padded_data) + encryptor.finalize()

    # End timing and calculate encryption duration
    encryption_end_time = time.time()
    encryption_duration = encryption_end_time - encryption_start_time
    total_encryption_time += encryption_duration

    print(f"[Client (Pi)] Frame {frame_count} Encryption Time: {encryption_duration:.6f} seconds")

    # Send Encrypted Frame to the Server
    payload = pickle.dumps((iv, encrypted_frame))
    client_socket.sendall(len(payload).to_bytes(4, 'big') + payload)
    frame_count += 1
    

    # Display metrics every 100 frames
    if frame_count == 100:
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # Memory in MB
        cpu_usage = psutil.cpu_percent(interval=0.1)
        average_encryption_time = total_encryption_time / frame_count

        print("\n[Metrics After 100 Frames]")
        print(f"Total Frames Processed: {frame_count}")
        print(f"Total Encryption Time: {total_encryption_time:.6f} seconds")
        print(f"Average Encryption Time per Frame: {average_encryption_time:.6f} seconds")
        print(f"Memory Usage: {memory_usage:.2f} MB")
        print(f"CPU Usage: {cpu_usage:.2f}%")
        print(f"---------------------------------")
        frame_count = 0;

    # Break on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
client_socket.close()
