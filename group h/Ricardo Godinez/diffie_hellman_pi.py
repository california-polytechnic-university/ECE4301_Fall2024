from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_OAEP
from hashlib import sha256
import socket
import os

def load_key(filename):
    with open(filename, 'rb') as f:
        return f.read()

def generate_random_secret():
    return os.urandom(32)  # 256-bit random secret

def hash_shared_secret(secret1, secret2):
    return sha256(secret1 + secret2).digest()

def exchange_keys(client_socket):
    # Send public key to server
    client_socket.send(load_key("public_key.pem"))

    # Receive public key from server
    server_public_key = client_socket.recv(4096)
    server_public_key = RSA.import_key(server_public_key)
    server_cipher = PKCS1_OAEP.new(server_public_key)

    # Generate and exchange secrets
    local_secret = generate_random_secret()
    encrypted_local_secret = server_cipher.encrypt(local_secret)
    client_socket.send(encrypted_local_secret)

    encrypted_remote_secret = client_socket.recv(4096)
    private_key = RSA.import_key(load_key("private_key.pem"))
    client_cipher = PKCS1_OAEP.new(private_key)
    remote_secret = client_cipher.decrypt(encrypted_remote_secret)

    # Create shared key
    shared_secret = hash_shared_secret(local_secret, remote_secret)
    return shared_secret

if __name__ == "__main__":
    HOST = '192.168.0.12'
    PORT = 8080

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        shared_key = exchange_keys(s)
        print(f"Shared key established: {shared_key.hex()}")
