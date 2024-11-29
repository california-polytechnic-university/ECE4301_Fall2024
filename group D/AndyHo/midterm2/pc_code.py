import cv2
import socket
import struct
import pickle
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import hashlib
import time


# Generate RSA Keys
def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key


# Serialize Public Key to PEM format
def serialize_public_key(public_key):
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


# Deserialize Public Key from PEM format
def deserialize_public_key(pem_data):
    return serialization.load_pem_public_key(pem_data)


# Calculate SHA-256 checksum
def calculate_checksum(data):
    """Calculate the SHA-256 checksum of the given data."""
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()


# Main Client Logic
def start_video_stream_client(server_ip):
    # Step 1: Generate RSA keys for the client
    private_key, public_key = generate_rsa_keys()

    # Step 2: Connect to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, 7878))  # Replace with server IP
    print("Connected to server.")

    # Step 3: Receive server's RSA public key
    server_public_key_pem = client_socket.recv(1024)
    server_public_key = deserialize_public_key(server_public_key_pem)
    print("Received server's RSA public key.")

    # Step 4: Send client's RSA public key
    client_public_key_pem = serialize_public_key(public_key)
    client_socket.sendall(client_public_key_pem)
    print("Client's RSA public key sent.")

    # Step 5: Receive encrypted AES key and nonce
    encrypted_key_nonce = client_socket.recv(512)  # Adjust size for RSA-encrypted data
    print("Received encrypted AES key and nonce.")

    # Step 6: Decrypt AES key and nonce using client's RSA private key
    key_nonce = private_key.decrypt(
        encrypted_key_nonce,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    aes_key = key_nonce[:32]  # 256-bit AES key
    aes_nonce = key_nonce[32:]  # 12-byte AES-GCM nonce
    print(f"Decrypted AES key: {aes_key.hex()}")
    print(f"Decrypted AES nonce: {aes_nonce.hex()}")

    # Step 7: Start receiving and decrypting video frames
    try:
        while True:
            print("Waiting to receive message size...")
            # Receive the size of the incoming encrypted frame (network byte order, 4 bytes)
            packed_msg_size = b""
            while len(packed_msg_size) < 4:
                more_data = client_socket.recv(4 - len(packed_msg_size))
                if not more_data:
                    print("Connection closed by server.")
                    return
                packed_msg_size += more_data

            msg_size = struct.unpack("!I", packed_msg_size)[0]
            print(f"Received encrypted message size: {msg_size} bytes")

            if msg_size <= 0 or msg_size > 50 * 10**6:
                print("Received an invalid message size. Breaking.")
                break

            # Receive the GCM authentication tag (16 bytes)
            gcm_tag = client_socket.recv(16)
            print(f"Received GCM authentication tag: {gcm_tag.hex()}")

            # Receive the encrypted frame data in chunks
            encrypted_data = b""
            while len(encrypted_data) < msg_size:
                packet = client_socket.recv(min(4096, msg_size - len(encrypted_data)))
                if not packet:
                    print("No data received. Breaking.")
                    return
                encrypted_data += packet
            print(f"Received encrypted frame data of size: {len(encrypted_data)} bytes")

            # Measure decryption time
            start_time = time.time()
            aes_cipher = Cipher(
                algorithms.AES(aes_key),
                modes.GCM(aes_nonce, gcm_tag),
                backend=default_backend(),
            )
            decryptor = aes_cipher.decryptor()

            try:
                decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
                decryption_time = time.time() - start_time
                decrypted_checksum = calculate_checksum(decrypted_data)
                print(f"Decryption time: {decryption_time:.6f} seconds")
                print(f"Decrypted checksum: {decrypted_checksum}")

                # Deserialize the frame
                frame = pickle.loads(decrypted_data)
                print("Frame decrypted and deserialized successfully.")

                # Display the video stream
                cv2.imshow('Received Video Stream', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Exiting video stream.")
                    break
            except Exception as e:
                print(f"Decryption failed: {e}")
                break

    except Exception as e:
        print(f"Exception occurred: {e}")

    finally:
        client_socket.close()
        cv2.destroyAllWindows()
        print("Client shut down.")


if __name__ == "__main__":
    raspberry_pi_ip = '192.168.254.66'  
    start_video_stream_client(raspberry_pi_ip)
