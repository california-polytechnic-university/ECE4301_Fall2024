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

# Generate RSA key pair for server
server_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
server_public_key = server_private_key.public_key()
server_public_key_serialized = server_public_key.public_bytes(
    encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Set up server
server_host, server_port = "0.0.0.0", 5000
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((server_host, server_port))
server_socket.listen(1)
connection, client_address = server_socket.accept()
connection.sendall(server_public_key_serialized)
client_public_key = serialization.load_pem_public_key(connection.recv(4096))

# Perform Diffie-Hellman key exchange
start_key_exchange = time.time()
client_random_bytes = server_private_key.decrypt(
    connection.recv(256), OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)
server_random_bytes = urandom(32)
connection.sendall(client_public_key.encrypt(
    server_random_bytes, OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
))
shared_encryption_key = HKDF(
    algorithm=hashes.SHA256(), length=32, salt=None, info=b'shared secret'
).derive(client_random_bytes + server_random_bytes)
end_key_exchange = time.time()

# Initialize AES encryption
initialization_vector = urandom(16)
aes_cipher = Cipher(algorithms.AES(shared_encryption_key), modes.CFB(initialization_vector))
aes_encryptor = aes_cipher.encryptor()
connection.sendall(initialization_vector)

# Set up camera
camera = Picamera2()
camera.configure(camera.create_video_configuration(main={"size": (640, 480)}))
camera.start()

frame_counter = 0
total_encryption_duration = 0
total_data_transferred = 0
start_streaming = time.time()

try:
    while True:
        # Capture frame from camera
        video_frame = cv2.cvtColor(camera.capture_array(), cv2.COLOR_BGR2RGB)
        frame_serialized = pickle.dumps(cv2.resize(video_frame, (640, 480)))

        # Encrypt frame
        start_encryption = time.time()
        encrypted_frame_data = aes_encryptor.update(frame_serialized)
        end_encryption = time.time()
        total_encryption_duration += end_encryption - start_encryption

        # Prepare frame payload
        frame_payload = pickle.dumps(encrypted_frame_data)
        frame_size = len(frame_payload)
        total_data_transferred += frame_size

        # Send frame
        connection.sendall(frame_size.to_bytes(4, 'big') + frame_payload)

        # Display encrypted video feed (optional)
        encrypted_display = np.frombuffer(encrypted_frame_data, dtype=np.uint8)[:640 * 480].reshape((480, 640))
        cv2.imshow("Encrypted Video Stream", encrypted_display)
        frame_counter += 1

        # Quit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
except:
    pass

# End streaming and calculate metrics
end_streaming = time.time()
total_streaming_duration = end_streaming - start_streaming
average_bandwidth_usage = total_data_transferred / total_streaming_duration

# Display streaming metrics
print(f"\n[Streaming Metrics]")
print(f"Key Exchange Duration: {end_key_exchange - start_key_exchange:.6f} seconds")
print(f"Total Encryption Duration: {total_encryption_duration:.6f} seconds")
print(f"Total Data Transferred: {total_data_transferred / 1_000_000:.2f} MB")
print(f"Average Bandwidth Usage: {average_bandwidth_usage / 1_000:.2f} KB/s")
print(f"Total Streaming Duration: {total_streaming_duration:.2f} seconds")

# Cleanup resources
camera.stop()
connection.close()
server_socket.close()
cv2.destroyAllWindows()
