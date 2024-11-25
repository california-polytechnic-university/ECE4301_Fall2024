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
from cryptography.hazmat.primitives.padding import PKCS7
import psutil  # For CPU and memory usage
import time  # For execution timing

# Metric tracking
transaction_times = []
decryption_times = []
frame_count = 0

# RSA Key Generation for the Server
keygen_start_time = time.time()
server_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
server_public_key = server_key.public_key()
keygen_end_time = time.time()
keygen_duration = keygen_end_time - keygen_start_time

# Serialize Public Key to Share with the Client
server_public_key_bytes = server_public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Print Server's Public Key
print("\n[Server (Laptop)] Public Key:")
print(server_public_key_bytes.decode())
print("[Server (Laptop)] Public Key Size:", server_key.key_size, "bits")

# Server Setup
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("192.168.1.213", 8000))  # Replace with your laptop's IP
server_socket.listen(1)
print("\n[Server (Laptop)] Waiting for connection from the Raspberry Pi...")

conn, addr = server_socket.accept()
print(f"\n[Server (Laptop)] Connection established with {addr}")

try:
    # Share Server's Public Key with the Client
    conn.sendall(server_public_key_bytes)

    # Receive Client's Public Key
    client_public_key_bytes = conn.recv(4096)
    client_public_key = serialization.load_pem_public_key(client_public_key_bytes)

    # Display Client's Public Key
    print("\n[Client (Pi)] Public Key:")
    print(client_public_key_bytes.decode())
    print("[Client (Pi)] Public Key Size:", client_public_key.key_size, "bits")

    # Start timing Diffie-Hellman
    dh_start_time = time.time()

    # Receive and Decrypt Client's Random Value
    encrypted_client_random = conn.recv(4096)
    client_random_value = server_key.decrypt(
        encrypted_client_random,
        OAEP(
            mgf=MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Generate Random Value and Encrypt with Client's Public Key
    server_random_value = urandom(32)
    encrypted_server_random = client_public_key.encrypt(
        server_random_value,
        OAEP(
            mgf=MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    conn.sendall(encrypted_server_random)

    # Derive Shared Secret
    shared_secret = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'shared secret'
    ).derive(client_random_value + server_random_value)

    # End timing Diffie-Hellman
    dh_end_time = time.time()
    dh_duration = dh_end_time - dh_start_time
    print(f"\n[Server (Laptop)] Diffie-Hellman Execution Time: {dh_duration:.6f} seconds")
    print("[Server (Laptop)] Shared Key Size: 256 bits")

    # Receive and Decrypt Video Frames
    while True:
        try:
            # Start timing the packet transaction
            transaction_start_time = time.time()

            # Receive frame size
            frame_size = int.from_bytes(conn.recv(4), 'big')
            if not frame_size:
                break

            # Receive frame payload
            payload = b""
            while len(payload) < frame_size:
                data = conn.recv(frame_size - len(payload))
                if not data:
                    raise ConnectionResetError("Connection lost while receiving frame.")
                payload += data

            transaction_end_time = time.time()
            transaction_duration = transaction_end_time - transaction_start_time
            transaction_times.append(transaction_duration)

            # Display transaction time for the frame
            print(f"[Server (Laptop)] Frame {frame_count + 1}: Transaction Packet Time: {transaction_duration:.6f} seconds")

            iv, encrypted_frame = pickle.loads(payload)

            # Start timing decryption in nanoseconds
            decryption_start_time_ns = time.perf_counter_ns()

            # AES Decryption
            cipher = Cipher(algorithms.AES(shared_secret), modes.CBC(iv))
            decryptor = cipher.decryptor()
            unpadder = PKCS7(algorithms.AES.block_size).unpadder()
            padded_data = decryptor.update(encrypted_frame) + decryptor.finalize()
            decrypted_frame = unpadder.update(padded_data) + unpadder.finalize()

            # End timing decryption in nanoseconds
            decryption_end_time_ns = time.perf_counter_ns()
            decryption_duration_ns = decryption_end_time_ns - decryption_start_time_ns
            decryption_times.append(decryption_duration_ns)

            # Display decryption time for the frame in nanoseconds
            print(f"[Server (Laptop)] Frame {frame_count + 1}: Decryption Time: {decryption_duration_ns} ns")

            # Decode and Display the Frame
            frame = cv2.imdecode(np.frombuffer(decrypted_frame, np.uint8), cv2.IMREAD_COLOR)
            cv2.imshow("Decrypted Video", frame)

            # Increment frame count
            frame_count += 1

            # Display metrics after 100 frames
            if frame_count == 100:
                # Calculate total and average metrics
                total_transaction_time = sum(transaction_times)
                total_decryption_time_ns = sum(decryption_times)
                avg_transaction_time = total_transaction_time / len(transaction_times)
                avg_decryption_time_ns = total_decryption_time_ns / len(decryption_times)

                # Fetch memory and CPU usage
                memory_usage = psutil.virtual_memory().percent
                cpu_usage = psutil.cpu_percent(interval=1)

                # Display results
                print("\n--- Metrics after 100 Frames ---")
                print(f"Memory Usage: {memory_usage:.2f}%")
                print(f"CPU Usage: {cpu_usage:.2f}%")
                print(f"Total Transaction Packet Time: {total_transaction_time:.6f} seconds")
                print(f"Total Decryption Time: {total_decryption_time_ns} ns")
                print(f"Avg Transaction Packet Time: {avg_transaction_time:.6f} seconds")
                print(f"Avg Decryption Time: {avg_decryption_time_ns} ns")
                print(f"Public and Shared Key Generation Time: {keygen_duration + dh_duration:.6f} seconds")
                frame_count = 0;

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except Exception as e:
            print(f"[Server (Laptop)] Error during frame handling: {e}")
            break

except Exception as e:
    print(f"[Server (Laptop)] Error: {e}")

finally:
    print("[Server (Laptop)] Closing connection.")
    conn.close()
    server_socket.close()
    cv2.destroyAllWindows()
