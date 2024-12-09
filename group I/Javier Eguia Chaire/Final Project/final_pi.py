import os
import socket
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.serialization import load_pem_public_key, Encoding, PublicFormat

# Generate RSA keys
server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
server_public_key = server_key.public_key()

# Serialize the public key
server_public_pem = server_public_key.public_bytes(
    encoding=Encoding.PEM,
    format=PublicFormat.SubjectPublicKeyInfo
)

# Set up the server
HOST = "0.0.0.0"
PORT = 5000
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"[Server] Listening on {HOST}:{PORT}")
conn, addr = server_socket.accept()
print(f"[Server] Connection established with {addr}")

# Send the server's public key to the client
conn.sendall(server_public_pem)

# Receive the client's public key
client_public_pem = conn.recv(4096)
client_public_key = load_pem_public_key(client_public_pem)

# Perform Diffie-Hellman-like exchange using RSA
server_random = os.urandom(32)
encrypted_client_random = conn.recv(256)
client_random = server_key.decrypt(
    encrypted_client_random,
    OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)

# Encrypt and send the server random
encrypted_server_random = client_public_key.encrypt(
    server_random,
    OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)
conn.sendall(encrypted_server_random)

# Derive a shared secret
shared_secret = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b'shared secret'
).derive(server_random + client_random)

# AES Setup
iv = os.urandom(16)
conn.sendall(iv)

# Default mode: CBC
current_mode = modes.CBC(iv)
cipher = Cipher(algorithms.AES(shared_secret), current_mode)
encryptor = cipher.encryptor()
decryptor = cipher.decryptor()

try:
    while True:
        # Receive command
        command = conn.recv(16).decode("utf-8").strip().upper()
        if command == "EXIT":
            print("[Server] Exiting.")
            break
        elif command == "SWITCH_MODE":
            # Switch between CBC and ECB
            if isinstance(current_mode, modes.CBC):
                current_mode = modes.ECB()
                print("[Server] Switched to ECB mode.")
            else:
                current_mode = modes.CBC(iv)
                print("[Server] Switched to CBC mode.")
            # Update cipher, encryptor, and decryptor
            cipher = Cipher(algorithms.AES(shared_secret), current_mode)
            encryptor = cipher.encryptor()
            decryptor = cipher.decryptor()
        elif command in ["ENCRYPT", "DECRYPT"]:
            # Receive file size and data
            file_size = int.from_bytes(conn.recv(4), 'big')
            data = conn.recv(file_size)

            if command == "ENCRYPT":
                processed_data = encryptor.update(data) + encryptor.finalize()
                print("[Server] Data encrypted.")
            elif command == "DECRYPT":
                processed_data = decryptor.update(data) + decryptor.finalize()
                print("[Server] Data decrypted.")

            # Send processed data back
            conn.sendall(len(processed_data).to_bytes(4, 'big'))
            conn.sendall(processed_data)
            print(f"[Server] {command}ed data sent back.")
        else:
            print(f"[Server] Invalid command received: {command}")

except Exception as e:
    print(f"[Server Error] {e}")

finally:
    conn.close()
    server_socket.close()
