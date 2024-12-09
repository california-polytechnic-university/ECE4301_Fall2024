import os
import cv2
import socket
import struct
import numpy as np
from ascon import ascon_decrypt
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Random import random
from hashlib import sha256
import time
import paramiko  # Added for SSH

# --------------------------
# Constants
# --------------------------
CHUNK_SIZE = 8192
GENERATOR = 2

# Pi SSH details
PI_HOST = 'PI IP'
PI_USERNAME = 'PI_Username'
PI_PASSWORD = 'PI_Password'
PI_VIDEO_STREAM_PATH = 'path_to_project'

# Performance metrics
metrics = {
    "encryption_time": [],
    "decryption_time": [],
    "key_exchange_time": 0,
    "transmission_time": [],
    "fps": 0,
    "pi_temperature": []
}

frame_counter = 0
fps_start_time = time.time()

# --------------------------
# Helper Functions
# --------------------------
def receive_exactly(conn, length):
    """Receive exactly length bytes from the connection."""
    data = b""
    while len(data) < length:
        packet = conn.recv(length - len(data))
        if not packet:
            raise ValueError("Connection closed before receiving expected data.")
        data += packet
    return data


def get_pi_temperature():
    """Retrieve the temperature of the Raspberry Pi."""
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(PI_HOST, username=PI_USERNAME, password=PI_PASSWORD)
    stdin, stdout, stderr = ssh_client.exec_command("vcgencmd measure_temp")
    temp_output = stdout.read().decode('utf-8').strip()
    ssh_client.close()
    return temp_output


def print_metrics():
    """Print the collected performance metrics."""
    print("\nPerformance Metrics:")
    print(f"Key Exchange Time: {metrics['key_exchange_time']:.4f} seconds")
    print(f"Average FPS: {metrics['fps']:.2f}")
    print(f"Average Decryption Time: {np.mean(metrics['decryption_time']):.4f} seconds")
    print(f"Average Transmission Time: {np.mean(metrics['transmission_time']):.4f} seconds")
    print(f"Pi Temperature: {metrics['pi_temperature'][-1] if metrics['pi_temperature'] else 'N/A'}")


def write_metrics_to_file():
    """Write performance metrics to a .txt file and automatically open it."""
    file_name = "secure_file_transfer_performance_metrics.txt"
    with open(file_name, "w") as f:
        f.write("Performance Metrics:\n")
        f.write(f"Key Exchange Time: {metrics['key_exchange_time']:.4f} seconds\n")
        f.write(f"Average FPS: {metrics['fps']:.2f}\n")
        f.write(f"Average Decryption Time: {np.mean(metrics['decryption_time']):.4f} seconds\n")
        f.write(f"Average Transmission Time: {np.mean(metrics['transmission_time']):.4f} seconds\n")
        f.write(f"Pi Temperature: {metrics['pi_temperature'][-1] if metrics['pi_temperature'] else 'N/A'}\n")
    print(f"\nPerformance metrics saved to '{file_name}'")

    # Automatically open the file
    try:
        if os.name == 'nt':  # For Windows
            os.startfile(file_name)
        elif os.name == 'posix':  # For macOS/Linux
            os.system(f"open '{file_name}'" if 'darwin' in os.uname().sysname.lower() else f"xdg-open '{file_name}'")
    except Exception as e:
        print(f"Unable to open the file automatically: {e}")


def ssh_into_pi_and_start_stream():
    """SSH into the Raspberry Pi and start the video streaming script."""
    print("Establishing SSH connection to the Raspberry Pi...")
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(PI_HOST, username=PI_USERNAME, password=PI_PASSWORD)
    print("SSH connection established.")

    # Start the video streaming script
    print("Starting video streaming script on the Raspberry Pi...")
    stdin, stdout, stderr = ssh_client.exec_command(f'python3 {PI_VIDEO_STREAM_PATH}')
    time.sleep(2)  # Allow time for the script to start
    return ssh_client

# --------------------------
# Main Function
# --------------------------
def decrypt_and_display_realtime(host="0.0.0.0", port=9999):
    global frame_counter, fps_start_time

    ssh_client = ssh_into_pi_and_start_stream()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    conn, addr = server_socket.accept()

    try:
        # Step 1: Key Exchange
        key_exchange_start = time.time()

        dh_public_key_size = struct.unpack("!I", receive_exactly(conn, 4))[0]
        dh_public_key_bytes = receive_exactly(conn, dh_public_key_size)
        dh_public_key_pi = int.from_bytes(dh_public_key_bytes, "big")

        prime_modulus_size = struct.unpack("!I", receive_exactly(conn, 4))[0]
        prime_modulus_bytes = receive_exactly(conn, prime_modulus_size)
        prime_modulus = int.from_bytes(prime_modulus_bytes, "big")

        print(f"Received DH Public Key: {dh_public_key_pi}, Size: {dh_public_key_pi.bit_length()} bits")
        print(f"Received Prime Modulus: {prime_modulus}, Size: {prime_modulus.bit_length()} bits")

        dh_private_key = random.getrandbits(256)
        dh_public_key = pow(GENERATOR, dh_private_key, prime_modulus)

        rsa_key = RSA.generate(2048)
        rsa_public_key = rsa_key.publickey().export_key(format='PEM')

        print(f"RSA Public Key (PEM Format):\n{rsa_public_key.decode('utf-8')}")

        conn.sendall(struct.pack("!I", len(rsa_public_key)))
        conn.sendall(rsa_public_key)

        rsa_cipher = PKCS1_OAEP.new(rsa_key)

        encrypted_pi_public_key_hash_size = struct.unpack("!I", receive_exactly(conn, 4))[0]
        encrypted_pi_public_key_hash = receive_exactly(conn, encrypted_pi_public_key_hash_size)

        pi_public_key_hash = rsa_cipher.decrypt(encrypted_pi_public_key_hash)
        expected_pi_public_key_hash = sha256(dh_public_key_bytes).digest()

        if pi_public_key_hash != expected_pi_public_key_hash:
            raise ValueError("Public key verification failed!")

        print(f"Decrypted Pi Public Key Hash: {pi_public_key_hash.hex()}")
        print("Public key verification successful.")

        dh_public_key_bytes = dh_public_key.to_bytes((dh_public_key.bit_length() + 7) // 8, "big")
        conn.sendall(struct.pack("!I", len(dh_public_key_bytes)))
        conn.sendall(dh_public_key_bytes)

        shared_key = pow(dh_public_key_pi, dh_private_key, prime_modulus)
        shared_key_bytes = shared_key.to_bytes((shared_key.bit_length() + 7) // 8, "big")[:16]

        key_exchange_end = time.time()
        metrics["key_exchange_time"] = key_exchange_end - key_exchange_start

        print(f"Shared key established: {shared_key_bytes.hex()}")

        # Step 2: Video Decryption and Display
        while True:
            transmission_start = time.time()

            # Periodically fetch and store Pi temperature
            if len(metrics["pi_temperature"]) == 0 or time.time() - fps_start_time >= 10:  # Every 10 seconds
                try:
                    pi_temp = get_pi_temperature()
                    metrics["pi_temperature"].append(pi_temp)
                    print(f"Pi Temperature: {pi_temp}")
                except Exception as e:
                    print(f"Error retrieving Pi temperature: {e}")

            frame_size_data = receive_exactly(conn, 4)
            if not frame_size_data:
                break
            frame_size = struct.unpack("!I", frame_size_data)[0]
            nonce = receive_exactly(conn, 16)
            encrypted_frame = receive_exactly(conn, frame_size - 16)

            transmission_end = time.time()
            metrics["transmission_time"].append(transmission_end - transmission_start)

            decryption_start = time.time()
            decrypted_data = ascon_decrypt(shared_key_bytes, nonce, b"", encrypted_frame)
            decryption_end = time.time()
            metrics["decryption_time"].append(decryption_end - decryption_start)

            frame = np.frombuffer(decrypted_data, dtype=np.uint8)
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

            if frame is not None:
                cv2.imshow("Decrypted Video", frame)

            frame_counter += 1
            elapsed_time = time.time() - fps_start_time
            if elapsed_time >= 1.0:
                metrics["fps"] = frame_counter / elapsed_time
                fps_start_time = time.time()
                frame_counter = 0

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print_metrics()
                write_metrics_to_file()
                break

    finally:
        conn.close()
        server_socket.close()
        cv2.destroyAllWindows()
        ssh_client.close()


# --------------------------
# Main Execution
# --------------------------
if __name__ == "__main__":
    try:
        print("Starting video stream decryption with RSA-encrypted Diffie-Hellman key exchange...")
        decrypt_and_display_realtime()
    except Exception as e:
        print(f"Error: {e}")
