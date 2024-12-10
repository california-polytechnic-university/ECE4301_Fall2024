from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
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

def exchange_keys(server_socket):
    # Receive public key from client
    client_public_key = server_socket.recv(4096)
    client_public_key = RSA.import_key(client_public_key)
    client_cipher = PKCS1_OAEP.new(client_public_key)
    
    # Send public key to client
    server_socket.send(load_key("public_key.pem"))
    
    # Generate and exchange secrets
    local_secret = generate_random_secret()
    encrypted_local_secret = client_cipher.encrypt(local_secret)
    server_socket.send(encrypted_local_secret)
    
    encrypted_remote_secret = server_socket.recv(4096)
    private_key = RSA.import_key(load_key("private_key.pem"))
    server_cipher = PKCS1_OAEP.new(private_key)
    remote_secret = server_cipher.decrypt(encrypted_remote_secret)
    
    # Create shared key
    shared_secret = hash_shared_secret(local_secret, remote_secret)
    return shared_secret

if __name__ == "__main__":
    HOST = '192.168.0.12'
    PORT = 8080
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("Waiting for connection...")
        conn, addr = s.accept()
        with conn:
            print(f"Connected to {addr}")
            shared_key = exchange_keys(conn)
            print(f"Shared key established: {shared_key.hex()}")
