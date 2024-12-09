import os
import socket
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, load_pem_public_key

# Generate RSA keys
client_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
client_public_key = client_key.public_key()

# Serialize the public key
client_public_pem = client_public_key.public_bytes(
    encoding=Encoding.PEM,
    format=PublicFormat.SubjectPublicKeyInfo
)

# Connect to the server
HOST = "192.168.50.219"  # Replace with server's IP
PORT = 5000
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# Receive server's public key
server_public_pem = client_socket.recv(4096)
server_public_key = load_pem_public_key(server_public_pem)

# Send client's public key
client_socket.sendall(client_public_pem)

# Perform Diffie-Hellman-like exchange using RSA
client_random = os.urandom(32)
encrypted_client_random = server_public_key.encrypt(
    client_random,
    OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)
client_socket.sendall(encrypted_client_random)

encrypted_server_random = client_socket.recv(256)
server_random = client_key.decrypt(
    encrypted_server_random,
    OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)

# Derive a shared secret
shared_secret = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b'shared secret'
).derive(client_random + server_random)

# AES Setup
iv = client_socket.recv(16)
mode = modes.CBC(iv)  # Default mode: CBC

try:
    while True:
        command = input("Enter command (ENCRYPT, DECRYPT, SWITCH_MODE, EXIT): ").strip().upper()
        if command == "EXIT":
            client_socket.sendall(command.encode().ljust(16, b' '))
            break
        elif command == "SWITCH_MODE":
            client_socket.sendall(command.encode().ljust(16, b' '))
            print("[Client] Requested to switch mode.")
        elif command in ["ENCRYPT", "DECRYPT"]:
            client_socket.sendall(command.encode().ljust(16, b' '))

            # Get file path
            file_path = input("Enter file path: ").strip()
            if not os.path.exists(file_path):
                print("[Client] File does not exist.")
                continue

            with open(file_path, "rb") as file:
                file_data = file.read()

            # Send file size and data
            client_socket.sendall(len(file_data).to_bytes(4, 'big'))
            client_socket.sendall(file_data)
            print(f"[Client] File sent for {command.lower()}ion.")

            # Receive processed file
            file_size = int.from_bytes(client_socket.recv(4), 'big')
            processed_data = client_socket.recv(file_size)

            # Save the processed file
            output_file = f"{command.lower()}ed_output.txt"
            with open(output_file, "wb") as output:
                output.write(processed_data)
            print(f"[Client] Processed file saved as '{output_file}'.")
        else:
            print("[Client] Invalid command.")

except Exception as e:
    print(f"[Client Error] {e}")

finally:
    client_socket.close()
