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
from picamera2 import Picamera2
import time

# RSA Key Generation
server_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
server_public_key = server_key.public_key()

# Serialize Public Key to Share with the Client
server_public_key_bytes = server_public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Set up the server
host = "0.0.0.0"  # Listen on all available interfaces
port = 5000  # Updated port for better performance
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(1)

print(f"[Server] Listening on {host}:{port}")
conn, addr = server_socket.accept()
print(f"[Server] Connection established with {addr}")

# Exchange RSA Keys
# Send Server's Public Key to the Client
conn.sendall(server_public_key_bytes)

# Receive Client's Public Key
client_public_key_bytes = conn.recv(4096)
client_public_key = serialization.load_pem_public_key(client_public_key_bytes)

# Diffie-Hellman: Exchange Random Values
start_time = time.time()

# Receive and Decrypt Client's Random Value
encrypted_client_random = conn.recv(256)  # Match RSA key size (256 bytes for 2048-bit keys)
try:
    client_random_value = server_key.decrypt(
        encrypted_client_random,
        OAEP(
            mgf=MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
except ValueError as e:
    print(f"[Server] Decryption error: {e}")
    conn.close()
    server_socket.close()
    exit()

# Generate Random Value and Encrypt with Client's Public Key
server_random_value = urandom(32)  # 32 bytes is safe for RSA encryption
encrypted_server_random = client_public_key.encrypt(
    server_random_value,
    OAEP(
        mgf=MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
conn.sendall(encrypted_server_random)

# Derive Shared Secret
shared_secret = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b'shared secret'
).derive(client_random_value + server_random_value)

end_time = time.time()
dh_execution_time = end_time - start_time
print(f"[Server] Shared Key Established in {dh_execution_time:.6f} seconds")

# AES Setup
iv = urandom(16)  # Initialization vector for AES-CFB
cipher = Cipher(algorithms.AES(shared_secret), modes.CFB(iv))
encryptor = cipher.encryptor()

# Send IV
conn.sendall(iv)

# Initialize the camera using Picamera2
camera = Picamera2()
camera_config = camera.create_video_configuration(main={"size": (640, 480)})  # Adjust resolution if needed
camera.configure(camera_config)
camera.start()

frame_count = 0
total_encryption_time = 0
total_bandwidth = 0
start_stream_time = time.time()

try:
    while True:
        # Capture a frame from the camera
        video_frame = camera.capture_array()

        # Convert the frame to RGB format (if needed)
        video_frame = cv2.cvtColor(video_frame, cv2.COLOR_BGR2RGB)

        # Resize the frame for consistency (if needed)
        resized_frame = cv2.resize(video_frame, (640, 480))

        # Serialize and encrypt frame
        frame_data = pickle.dumps(resized_frame)
        encryption_start_time = time.time()
        encrypted_frame = encryptor.update(frame_data)
        encryption_end_time = time.time()

        # Calculate encryption time
        encryption_time = encryption_end_time - encryption_start_time
        total_encryption_time += encryption_time

        # Send encrypted frame
        payload = pickle.dumps(encrypted_frame)
        frame_size = len(payload)
        total_bandwidth += frame_size
        transaction_start_time = time.time()
        conn.sendall(frame_size.to_bytes(4, 'big') + payload)
        transaction_end_time = time.time()

        # Calculate transaction time
        transaction_time = transaction_end_time - transaction_start_time
        print(f"[Server] Frame {frame_count}: Transaction Time: {transaction_time:.6f} seconds")

        # Display the encrypted video locally
        encrypted_display = np.frombuffer(encrypted_frame, dtype=np.uint8)
        encrypted_display = encrypted_display[:640 * 480].reshape((480, 640))  # Adjust dimensions for grayscale display
        cv2.imshow("Encrypted Video", encrypted_display)

        frame_count += 1

        # Exit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print(f"[Server] Error: {e}")
finally:
    # Calculate total stream time and bandwidth
    end_stream_time = time.time()
    total_stream_time = end_stream_time - start_stream_time
    bandwidth_usage = total_bandwidth / total_stream_time

    print(f"\n[Server Metrics]")
    print(f"Diffie-Hellman Execution Time: {dh_execution_time:.6f} seconds")
    print(f"Total Encryption Time: {total_encryption_time:.6f} seconds")
    print(f"Total Bandwidth Used: {total_bandwidth / 1_000_000:.2f} MB")
    print(f"Average Bandwidth Usage: {bandwidth_usage / 1_000:.2f} KB/s")
    print(f"Total Streaming Time: {total_stream_time:.2f} seconds")

    camera.stop()
    conn.close()
    server_socket.close()
    cv2.destroyAllWindows()
