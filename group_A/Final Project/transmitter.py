import socket
import pyaudio
import sys
import time
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization
import os

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 256

def ensure_metrics_file():
    if not os.path.exists("metrics.log"):
        with open("metrics.log", "w") as f:
            f.write("Timestamp,Message\n")

def log_metric(message):
    with open("metrics.log", "a") as f:
        f.write(f"{datetime.now()}: {message}\n")

def encrypt_data(key, nonce, data):
    start_time = time.time()
    try:
        cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
        encrypted_data = cipher.encryptor().update(data)
        log_metric(f"Encryption time: {time.time() - start_time:.6f} seconds")
        return encrypted_data
    except Exception as e:
        print(f"Error encrypting data: {e}")
        return b''

def sign_data(private_key, data):
    start_time = time.time()
    try:
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        log_metric(f"Signing time: {time.time() - start_time:.6f} seconds")
        return signature
    except Exception as e:
        print(f"Error signing data: {e}")
        return b''

def send_audio(target_ip, target_port, local_port, key, nonce, private_key):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', local_port))
        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        print(f"Transmitter sending encrypted audio to {target_ip}:{target_port} from local port {local_port}...")
        try:
            while True:
                data = stream.read(CHUNK, exception_on_overflow=False)
                encrypted_data = encrypt_data(key, nonce, data)
                signature = sign_data(private_key, encrypted_data)
                start_time = time.time()
                sock.sendto(signature + encrypted_data, (target_ip, target_port))
                log_metric(f"Sending time: {time.time() - start_time:.6f} seconds")
        except KeyboardInterrupt:
            print("Stopping transmitter...")
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()
            sock.close()
    except Exception as e:
        print(f"Error in send_audio: {e}")

if __name__ == "__main__":
    ensure_metrics_file()
    if len(sys.argv) != 7:
        print("Usage: python transmitter.py <target_ip> <target_port> <local_port> <key> <nonce> <private_key_path>")
        sys.exit(1)
    with open(sys.argv[6], "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)
    with open("peer_public_key.pem", "rb") as key_file:
        client_public_key = serialization.load_pem_public_key(key_file.read())
    send_audio(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), bytes.fromhex(sys.argv[4]), bytes.fromhex(sys.argv[5]), private_key)
