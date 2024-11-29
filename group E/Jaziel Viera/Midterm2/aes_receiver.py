import cv2
import socket
import pickle
import numpy as np
from os import urandom
from time import time
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# Generate client's RSA key pair
client_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
client_public_key = client_private_key.public_key()
client_public_key_serialized = client_public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Connect to the server
server_host, server_port = "192.168.1.114", 5000
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((server_host, server_port))

# Exchange public keys
server_public_key_serialized = client_socket.recv(4096)
server_public_key = serialization.load_pem_public_key(server_public_key_serialized)
client_socket.sendall(client_public_key_serialized)

# Perform key exchange
start_time = time()
client_random_bytes = urandom(32)
encrypted_client_random_bytes = server_public_key.encrypt(
    client_random_bytes,
    OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)
key_encryption_duration = time() - start_time

client_socket.sendall(encrypted_client_random_bytes)

start_time = time()
server_random_bytes = client_private_key.decrypt(
    client_socket.recv(256),
    OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)
key_decryption_duration = time() - start_time

# Derive shared encryption key
start_time = time()
shared_encryption_key = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b'shared secret'
).derive(client_random_bytes + server_random_bytes)
key_derivation_duration = time() - start_time

# Receive initialization vector (IV) and set up AES decryption
initialization_vector = client_socket.recv(16)
aes_cipher = Cipher(algorithms.AES(shared_encryption_key), modes.CFB(initialization_vector))
aes_decryptor = aes_cipher.decryptor()

# Display metrics
metrics_window_name = "Performance Metrics"
cv2.namedWindow(metrics_window_name, cv2.WINDOW_NORMAL)

# Video feed loop
frame_counter = 0
while True:
    # Read frame size
    frame_length = int.from_bytes(client_socket.recv(4), 'big')
    if frame_length == 0:
        break

    # Receive encrypted frame payload
    encrypted_frame_payload = b""
    while len(encrypted_frame_payload) < frame_length:
        chunk = client_socket.recv(frame_length - len(encrypted_frame_payload))
        if not chunk:
            client_socket.close()
            exit()
        encrypted_frame_payload += chunk

    # Deserialize and decrypt the frame
    encrypted_frame_data = pickle.loads(encrypted_frame_payload)

    start_time = time()
    decrypted_frame_data = aes_decryptor.update(encrypted_frame_data)
    frame_decryption_duration = time() - start_time

    frame = pickle.loads(decrypted_frame_data)
    frame_counter += 1

    # Display the decrypted video
    cv2.imshow("Decrypted Video Stream", frame)

    # Display metrics in a separate window
    metrics_display = np.zeros((500, 600, 3), dtype=np.uint8)
    metrics_info = [
        f"Key Derivation Time: {key_derivation_duration:.6f} sec",
        f"Frame Decryption Time: {frame_decryption_duration:.6f} sec",
        f"Total Frames Processed: {frame_counter}",
    ]
    for i, metric in enumerate(metrics_info):
        cv2.putText(metrics_display, metric, (10, 50 + i * 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imshow(metrics_window_name, metrics_display)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

client_socket.close()
cv2.destroyAllWindows()
