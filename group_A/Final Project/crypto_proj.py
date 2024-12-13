import os
import signal
import subprocess
import socket
import random
import time
from time import sleep
from threading import Thread
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from sympy import randprime
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from datetime import datetime

# Constants
HOST = '0.0.0.0'  # Listen on all available interfaces
TCP_PORT = 5000  # TCP port for initial connection
NONCE = b'1234567890123456'  # Nonce for encryption

# Global Variables
current_process = None  # Current subprocess
is_transmitter = False  # Mode flag
target_ip = None  # Target IP address
UDP_PORT_RX = None  # UDP port for receiving
UDP_PORT_TX = None  # UDP port for transmitting
shared_key = None  # Shared encryption key

def stop_current_process():
    global current_process
    if current_process:
        try:
            print("Stopping current process...")
            current_process.terminate()
            current_process.wait()
            current_process = None
        except Exception as e:
            print(f"Error stopping process: {e}")

def ensure_metrics_file():
    if not os.path.exists("metrics.log"):
        with open("metrics.log", "w") as f:
            f.write("Timestamp,Message\n")

def log_metric(message):
    with open("metrics.log", "a") as f:
        f.write(f"{datetime.now()}: {message}\n")

def generate_rsa_keys():
    if not os.path.exists("private_key.pem") or not os.path.exists("public_key.pem"):
        start_time = time.time()
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            public_key = private_key.public_key()
            with open("private_key.pem", "wb") as private_file:
                private_file.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            with open("public_key.pem", "wb") as public_file:
                public_file.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            print("RSA key pair generated and saved as private_key.pem and public_key.pem.")
            log_metric(f"RSA key generation time: {time.time() - start_time:.6f} seconds")
        except Exception as e:
            print(f"Error generating RSA keys: {e}")
    else:
        print("RSA key pair already exists. Skipping generation.")

def start_process(mode):
    global current_process, target_ip, UDP_PORT_RX, UDP_PORT_TX, shared_key
    try:
        print(f"Starting {mode}...")
        args = ["python", f"{mode}.py"]
        if mode == "receiver":
            # Pass arguments to receiver script
            args.extend([str(UDP_PORT_RX), shared_key.hex(), NONCE.hex(), "public_key.pem"])
        elif mode == "transmitter":
            # Pass arguments to transmitter script
            args.extend([target_ip, str(UDP_PORT_RX), str(UDP_PORT_TX), shared_key.hex(), NONCE.hex(), "private_key.pem"])
        current_process = subprocess.Popen(args, preexec_fn=os.setsid if os.name != 'nt' else None)
    except Exception as e:
        print(f"Error starting process: {e}")

def toggle_mode():
    global is_transmitter
    is_transmitter = not is_transmitter
    stop_current_process()
    print("Mode changed.")
    start_process("transmitter" if is_transmitter else "receiver")

def listen_for_input():
    while True:
        try:
            if input("\nPress 't' to toggle modes (transmitter/receiver): ").strip().lower() == 't':
                toggle_mode()
        except Exception as e:
            print(f"Error listening for input: {e}")

def generate_public_key(p=None, g=None):
    # Generate random large prime numbers for Diffie-Hellman Parameters
    if p is None or g is None:
        p = randprime(2**30 - 1, 2**32 - 1)  # Example range, adjust as needed
        g = randprime(2, p)  # Generator should be a prime less than p
    private_key = random.randint(1, p - 2)  # Private key for Diffie-Hellman
    public_key = pow(g, private_key, p)  # Public key for Diffie-Hellman
    print(f"Generated parameters: p={p}, g={g}, private_key={private_key}, public_key={public_key}")
    return p, g, private_key, public_key

def generate_shared_key(peer_public_key, private_key, p):
    global shared_key
    try:
        # Generate shared secret using peer's public key
        shared_secret = pow(peer_public_key, private_key, p)
        print(f"Calculated shared secret: {shared_secret}")
        # Derive shared key using HKDF
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"ChaCha20 key derivation"
        )
        shared_key = hkdf.derive(shared_secret.to_bytes((shared_secret.bit_length() + 7) // 8, 'big'))
        print(f"Shared ChaCha20 key derived. Key={shared_key.hex()}")
    except Exception as e:
        print(f"Error generating shared key: {e}")

def establish_connection():
    global target_ip, UDP_PORT_RX, UDP_PORT_TX, p, g  # Add p and g to the global variables
    role = input("Enter 'server' to host or 'client' to connect: ").strip().lower()
    if role == "server":
        try:
            print("Starting server...")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind((HOST, TCP_PORT))
                server_socket.listen(1)
                print(f"Server listening on {HOST}:{TCP_PORT}...")
                conn, addr = server_socket.accept()
                print(f"Connection established with {addr}.")
                target_ip = addr[0]
                p, g, private_key, public_key = generate_public_key()
                print(f"Sending parameters to client: p={p}, g={g}, public_key={public_key}")
                conn.sendall(f"{p},{g},{public_key}".encode())
                client_public_key = int(conn.recv(1024).decode())
                print(f"Received public key from client: {client_public_key}")
                generate_shared_key(client_public_key, private_key, p)
                UDP_PORT_RX, UDP_PORT_TX = random.randint(1024, 65535), random.randint(1024, 65535)
                conn.sendall(f"{UDP_PORT_RX},{UDP_PORT_TX}".encode())
                
                # Send RSA public key to client
                with open("public_key.pem", "rb") as public_file:
                    rsa_public_key = public_file.read()
                conn.sendall(rsa_public_key)
                
                # Receive RSA public key from client
                client_rsa_public_key = conn.recv(2048)
                with open("peer_public_key.pem", "wb") as client_public_file:
                    client_public_file.write(client_rsa_public_key)
                
                return True
        except (ConnectionResetError, ConnectionAbortedError):
            print("Connection lost. Exiting...")
            return False
        except Exception as e:
            print(f"Error establishing server connection: {e}")
            return False
    elif role == "client":
        try:
            target_ip = input("Enter the server IP address: ").strip()
            print(f"Connecting to server at {target_ip}:{TCP_PORT}...")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((target_ip, TCP_PORT))
                print("Connected to server.")
                p, g, server_public_key = map(int, client_socket.recv(1024).decode().split(','))
                print(f"Received parameters from server: p={p}, g={g}, public_key={server_public_key}")
                _, _, private_key, public_key = generate_public_key(p, g)
                print(f"Sending public key to server: {public_key}")
                client_socket.sendall(str(public_key).encode())
                generate_shared_key(server_public_key, private_key, p)
                UDP_PORT_RX, UDP_PORT_TX = map(int, client_socket.recv(1024).decode().split(','))
                print(f"Assigned ports: Receiver={UDP_PORT_RX}, Transmitter={UDP_PORT_TX}")
                
                # Receive RSA public key from server
                server_rsa_public_key = client_socket.recv(2048)
                with open("peer_public_key.pem", "wb") as server_public_file:
                    server_public_file.write(server_rsa_public_key)
                
                # Send RSA public key to server
                with open("public_key.pem", "rb") as public_file:
                    rsa_public_key = public_file.read()
                client_socket.sendall(rsa_public_key)
                
                return True
        except (ConnectionResetError, ConnectionAbortedError):
            print("Connection lost. Exiting...")
            return False
        except Exception as e:
            print(f"Error establishing client connection: {e}")
            return False
    else:
        print("Invalid role. Please choose 'server' or 'client'.")
        return False

def main():
    generate_rsa_keys()
    if not establish_connection():
        print("Connection establishment failed. Exiting...")
        return
    print("Starting in receiver mode...")
    start_process("receiver")
    if os.name == 'nt':
        Thread(target=listen_for_input, daemon=True).start()
    else:
        from gpiozero import Button
        button = Button(2)
        button.when_pressed = toggle_mode
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        stop_current_process()

if __name__ == "__main__":
    ensure_metrics_file()
    main()
