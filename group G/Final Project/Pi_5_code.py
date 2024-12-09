import os
import cv2
import socket
import struct
from ascon import ascon_encrypt
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Util.number import getPrime
from Crypto.Random import random
from hashlib import sha256
import time

# --------------------------
# Constants
# --------------------------
CHUNK_SIZE = 8192  # Chunk size in bytes
PRIME_BITS = 2048  # Size of the prime modulus for Diffie-Hellman
GENERATOR = 2      # Generator for Diffie-Hellman

# --------------------------
# Helper Functions
# --------------------------
def receive_exactly(conn, length):
    """Receive exactly `length` bytes from the connection."""
    data = b""
    while len(data) < length:
        packet = conn.recv(length - len(data))
        if not packet:
            raise ValueError("Connection closed before receiving expected data.")
        data += packet
    return data

# --------------------------
# Generate Diffie-Hellman Keys
# --------------------------
def generate_dh_keys():
    private_key = random.getrandbits(256)  # Random private key
    prime_modulus = getPrime(PRIME_BITS)  # Large random prime modulus
    public_key = pow(GENERATOR, private_key, prime_modulus)
    return private_key, public_key, prime_modulus

# --------------------------
# Camera Initialization
# --------------------------
def initialize_camera():
    """Initialize and verify the camera."""
    cap = cv2.VideoCapture(0)
    retries = 5
    while not cap.isOpened() and retries > 0:
        print("Retrying camera initialization...")
        cap = cv2.VideoCapture(0)
        retries -= 1
    if not cap.isOpened():
        raise RuntimeError("Could not open camera after multiple retries.")
    return cap

# --------------------------
# Video Capture and Encryption
# --------------------------
def capture_and_send_realtime(host="laptop_ip", port=9999):
    cap = initialize_camera()

    print("Starting video capture and encryption...")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        print(f"Connected to laptop on {host}:{port}.")

        # Step 1: Generate Diffie-Hellman keys
        print("Generating Diffie-Hellman keys...")
        dh_private_key, dh_public_key, prime_modulus = generate_dh_keys()

        # Debugging: Log DH key sizes
        print(f"DH Public Key: {dh_public_key}, Size: {dh_public_key.bit_length()} bits")
        print(f"Prime Modulus: {prime_modulus}, Size: {prime_modulus.bit_length()} bits")

        # Step 2: Send public key and prime modulus to the laptop
        dh_public_key_bytes = dh_public_key.to_bytes((dh_public_key.bit_length() + 7) // 8, "big")
        prime_modulus_bytes = prime_modulus.to_bytes((prime_modulus.bit_length() + 7) // 8, "big")
        client_socket.sendall(struct.pack("!I", len(dh_public_key_bytes)))
        client_socket.sendall(dh_public_key_bytes)
        client_socket.sendall(struct.pack("!I", len(prime_modulus_bytes)))
        client_socket.sendall(prime_modulus_bytes)

        # Step 3: Receive RSA public key
        print("Receiving RSA public key...")
        rsa_key_size = struct.unpack("!I", receive_exactly(client_socket, 4))[0]
        rsa_key_bytes = receive_exactly(client_socket, rsa_key_size)

        # Debugging: Verify received RSA public key
        print(f"Received RSA Public Key Size: {len(rsa_key_bytes)} bytes")

        # Attempt to import the RSA public key
        try:
            laptop_rsa_public_key = RSA.import_key(rsa_key_bytes)
            print("Successfully imported RSA public key.")
        except ValueError as e:
            print(f"Error importing RSA public key: {e}")
            return

        # Step 4: Hash and send Pi's public key
        print("Hashing and encrypting Pi's public key...")
        dh_public_key_hash = sha256(dh_public_key_bytes).digest()
        rsa_cipher = PKCS1_OAEP.new(laptop_rsa_public_key)
        encrypted_public_key_hash = rsa_cipher.encrypt(dh_public_key_hash)
        client_socket.sendall(struct.pack("!I", len(encrypted_public_key_hash)))
        client_socket.sendall(encrypted_public_key_hash)

        # Step 5: Receive laptop's public key and compute shared key
        print("Receiving laptop's public key...")
        laptop_public_key_size = struct.unpack("!I", receive_exactly(client_socket, 4))[0]
        laptop_public_key_bytes = receive_exactly(client_socket, laptop_public_key_size)
        laptop_public_key = int.from_bytes(laptop_public_key_bytes, "big")

        shared_key = pow(laptop_public_key, dh_private_key, prime_modulus)
        shared_key_bytes = shared_key.to_bytes((shared_key.bit_length() + 7) // 8, "big")[:16]  # Use first 16 bytes
        print(f"Shared key established: {shared_key_bytes.hex()}")

        # Step 6: Capture, encrypt, and send video frames
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame from camera.")
                break

            # Compress the frame
            frame = cv2.resize(frame, (320, 240))  # Reduce resolution to 320x240
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            _, compressed_frame = cv2.imencode(".jpg", frame, encode_param)

            # Encrypt the compressed frame
            nonce = os.urandom(16)
            encrypted_frame = ascon_encrypt(shared_key_bytes, nonce, b"", compressed_frame.tobytes())

            # Calculate total frame size (nonce + encrypted frame)
            frame_size = len(encrypted_frame) + len(nonce)
            frame_header = struct.pack("!I", frame_size)

            # Send frame header
            client_socket.sendall(frame_header)

            # Send nonce
            client_socket.sendall(nonce)

            # Send encrypted frame in chunks
            for i in range(0, len(encrypted_frame), CHUNK_SIZE):
                chunk = encrypted_frame[i:i + CHUNK_SIZE]
                client_socket.sendall(chunk)

            print(f"Encrypted and sent frame. Compressed size: {len(compressed_frame)} bytes.")
    except Exception as e:
        print(f"Error during execution: {e}")
    finally:
        cap.release()
        client_socket.close()

# --------------------------
# Main Execution
# --------------------------
if __name__ == "__main__":
    try:
        print("Starting video stream encryption with RSA-encrypted Diffie-Hellman key exchange...")
        capture_and_send_realtime()
    except Exception as e:
        print(f"Error during execution: {e}")
