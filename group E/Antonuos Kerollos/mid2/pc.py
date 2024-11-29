# laptop_client.py
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
import time

# RSA Key Generation
client_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048  # Ensure it matches the server's key size
)
client_public_key = client_key.public_key()

# Serialize Public Key to Share with the Server
client_public_key_bytes = client_public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Connect to the server
host = "192.168.1.99"  # Replace with the Raspberry Pi's IP
port = 5000
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect((host, port))
    print(f"[Client] Connected to {host}:{port}")
except Exception as e:
    print(f"[Client] Connection Error: {e}")
    exit()

# Exchange RSA Keys
# Receive Server's Public Key
server_public_key_bytes = client_socket.recv(4096)
server_public_key = serialization.load_pem_public_key(server_public_key_bytes)

# Send Client's Public Key to the Server
client_socket.sendall(client_public_key_bytes)

# Diffie-Hellman: Exchange Random Values
start_time = time.time()

# Generate Random Value and Encrypt with Server's Public Key
client_random_value = urandom(32)  # Safe size for RSA encryption
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
encrypted_server_random = client_socket.recv(256)  # Match RSA key size (256 bytes for 2048-bit keys)
try:
    server_random_value = client_key.decrypt(
        encrypted_server_random,
        OAEP(
            mgf=MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
except ValueError as e:
    print(f"[Client] Decryption error: {e}")
    client_socket.close()
    exit()

# Derive Shared Secret
shared_secret = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b'shared secret'
).derive(client_random_value + server_random_value)

end_time = time.time()
print(f"[Client] Shared Key Established in {end_time - start_time:.6f} seconds")

# AES Setup
iv = client_socket.recv(16)  # Receive Initialization Vector
cipher = Cipher(algorithms.AES(shared_secret), modes.CFB(iv))
decryptor = cipher.decryptor()

# Receive and display video frames
frame_count = 0
while True:
    try:
        # Receive frame size
        frame_size = int.from_bytes(client_socket.recv(4), 'big')
        if frame_size == 0:
            break

        # Receive frame payload
        payload = b""
        while len(payload) < frame_size:
            data = client_socket.recv(frame_size - len(payload))
            if not data:
                raise ConnectionResetError("Connection lost while receiving frame.")
            payload += data

        # Deserialize and decrypt frame
        encrypted_frame = pickle.loads(payload)
        decrypted_frame_data = decryptor.update(encrypted_frame)
        frame = pickle.loads(decrypted_frame_data)

        # Display frame
        cv2.imshow("Decrypted Video", frame)
        frame_count += 1

        # Print frame count for debugging
        if frame_count % 100 == 0:
            print(f"[Client] Frames Processed: {frame_count}")

        # Exit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    except Exception as e:
        print(f"[Client] Error: {e}")
        break

client_socket.close()
cv2.destroyAllWindows()
