import cv2
import socket
import struct
import pickle
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import hashlib
import time

def calculate_checksum(data):
    """Calculate the SHA-256 checksum of the given data."""
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()

def start_video_stream_client(pi_ip):
    print("Starting client...")
    # Set up the client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((pi_ip, 8080))
        print(f"Connected to server at {pi_ip}:8080")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # Receive the key and nonce from the server (for testing purposes only, do this securely in production)
    key_nonce = client_socket.recv(32 + 16)  # 32 bytes for key, 16 bytes for nonce
    key = key_nonce[:32]
    nonce = key_nonce[32:]

    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
    decryptor = cipher.decryptor()

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

            # Receive the encrypted frame data in chunks
            encrypted_data = b""
            while len(encrypted_data) < msg_size:
                packet = client_socket.recv(min(4096, msg_size - len(encrypted_data)))
                if not packet:
                    print("No data received. Breaking.")
                    return
                encrypted_data += packet
            print(f"Received encrypted frame data of size: {len(encrypted_data)} bytes")

            # Calculate checksum of the received encrypted data
            received_encrypted_checksum = calculate_checksum(encrypted_data)
            print(f"Received encrypted checksum: {received_encrypted_checksum}")

            # Measure decryption time
            start_time = time.time()
            decrypted_data = decryptor.update(encrypted_data)
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
        print(f"Exception occurred: {e}")

    finally:
        client_socket.close()
        cv2.destroyAllWindows()
        print("Client shut down.")

if __name__ == "__main__":
    raspberry_pi_ip = '192.168.254.66'  # Replace with your Raspberry Pi's IP address
    start_video_stream_client(raspberry_pi_ip)
