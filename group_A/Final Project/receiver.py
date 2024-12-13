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

def decrypt_data(key, nonce, data):
    start_time = time.time()
    try:
        cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
        decrypted_data = cipher.decryptor().update(data)
        log_metric(f"Decryption time: {time.time() - start_time:.6f} seconds")
        return decrypted_data
    except Exception as e:
        print(f"Error decrypting data: {e}")
        return b''

def verify_signature(public_key, signature, data):
    start_time = time.time()
    try:
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        log_metric(f"Signature verification time: {time.time() - start_time:.6f} seconds")
        return True
    except Exception as e:
        print(f"Error verifying signature: {e}")
        print(f"Signature: {signature.hex()}")
        print(f"Data: {data.hex()}")
        return False

def receive_audio(port, key, nonce, public_key):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', port))
        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
        print(f"Receiver started on port {port}, waiting for encrypted audio...")
        try:
            while True:
                encrypted_data, _ = sock.recvfrom(4096)  # Increase buffer size
                signature_length = public_key.key_size // 8  # Calculate signature length
                signature, encrypted_data = encrypted_data[:signature_length], encrypted_data[signature_length:]
                if verify_signature(public_key, signature, encrypted_data):
                    stream.write(decrypt_data(key, nonce, encrypted_data))
                else:
                    print("Invalid signature. Data discarded.")
        except KeyboardInterrupt:
            print("Stopping receiver...")
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()
            sock.close()
    except Exception as e:
        print(f"Error in receive_audio: {e}")

if __name__ == "__main__":
    ensure_metrics_file()
    if len(sys.argv) != 5:
        print("Usage: python receiver.py <port> <key> <nonce> <public_key_path>")
        sys.exit(1)
    with open(sys.argv[4], "rb") as key_file:
        public_key = serialization.load_pem_public_key(key_file.read())
    with open("peer_public_key.pem", "rb") as key_file:
        server_public_key = serialization.load_pem_public_key(key_file.read())
    receive_audio(int(sys.argv[1]), bytes.fromhex(sys.argv[2]), bytes.fromhex(sys.argv[3]), server_public_key)
