# sender.py
import cv2
import socket
import time
import struct
import threading
import os
import numpy as np
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding as asym_padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

# Choose AES mode (CBC, CFB, GCM)
AES_MODE = AES.MODE_CBC  # You can change this to AES.MODE_CFB, AES.MODE_GCM, etc.

# Variables for performance metrics
key_exchange_time = 0
packet_transmission_times = []
ecdh_key_size = 0

def attempt_camera_open():
    while True:
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise Exception("Could not open video device")
            else:
                print("Camera opened successfully")
                return cap
        except Exception as e:
            print("Failed to open camera: ", e)
            time.sleep(1)

def send_video(s, aes_key):
    cap = attempt_camera_open()
    frame_count = 0
    while True:
        try:
            start_time = time.time()
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break

            # Encode frame
            frame_bytes = cv2.imencode('.jpg', frame)[1].tobytes()

            # AES Encryption
            iv = os.urandom(16)
            cipher = AES.new(aes_key, AES_MODE, iv)
            ciphertext = cipher.encrypt(pad(frame_bytes, AES.block_size))

            # Prepare data
            data = iv + ciphertext
            data_length = len(data)

            # Send data length
            s.sendall(struct.pack('!I', data_length))

            # Send data
            s.sendall(data)

            end_time = time.time()
            transmission_time = end_time - start_time
            packet_transmission_times.append(transmission_time)
            frame_count += 1

            # Display performance metrics every 30 frames
            if frame_count % 30 == 0:
                avg_trans_time = sum(packet_transmission_times[-30:]) / 30
                print(f"Avg Packet Transmission Time (last 30 frames): {avg_trans_time:.4f} seconds")
        except Exception as e:
            print("Error during video transmission: ", e)
            break
    cap.release()

def key_exchange(s):
    global key_exchange_time, ecdh_key_size
    try:
        start_time = time.time()
        # Generate RSA keys
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()

        # Send RSA public key
        rpi_public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        s.sendall(struct.pack('!I', len(rpi_public_key_pem)))
        s.sendall(rpi_public_key_pem)

        # Receive PC's RSA public key
        pc_public_key_length = struct.unpack('!I', s.recv(4))[0]
        pc_public_key_pem = s.recv(pc_public_key_length)
        pc_public_key = serialization.load_pem_public_key(
            pc_public_key_pem,
            backend=default_backend()
        )

        # Generate ECDH private key
        rpi_private_key_ecdh = ec.generate_private_key(ec.SECP256R1(), backend=default_backend())
        rpi_public_key_ecdh = rpi_private_key_ecdh.public_key()

        # Serialize ECDH public key
        rpi_public_key_ecdh_bytes = rpi_public_key_ecdh.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        ecdh_key_size = len(rpi_public_key_ecdh_bytes) * 8  # in bits

        # Encrypt and send ECDH public key
        encrypted_rpi_public_key_ecdh = pc_public_key.encrypt(
            rpi_public_key_ecdh_bytes,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        s.sendall(struct.pack('!I', len(encrypted_rpi_public_key_ecdh)))
        s.sendall(encrypted_rpi_public_key_ecdh)

        # Receive and decrypt PC's ECDH public key
        encrypted_pc_public_key_length = struct.unpack('!I', s.recv(4))[0]
        encrypted_pc_public_key_ecdh = s.recv(encrypted_pc_public_key_length)
        pc_public_key_ecdh_bytes = private_key.decrypt(
            encrypted_pc_public_key_ecdh,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        pc_public_key_ecdh = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), pc_public_key_ecdh_bytes)

        # Generate shared secret
        shared_key = rpi_private_key_ecdh.exchange(ec.ECDH(), pc_public_key_ecdh)

        # Derive AES key
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'handshake data',
            backend=default_backend()
        ).derive(shared_key)

        end_time = time.time()
        key_exchange_time = end_time - start_time
        print(f"Key exchange successful in {key_exchange_time:.4f} seconds")
        return derived_key
    except Exception as e:
        print("Key exchange failed: ", e)
        s.close()
        exit(1)

def main():
    HOST = '192.168.50.97'
    PORT = 65432

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        print("Connected to PC")
    except Exception as e:
        print("Connection to PC failed: ", e)
        exit(1)

    aes_key = key_exchange(s)

    # Send ECDH key size to PC for numerical evaluation
    s.sendall(struct.pack('!I', ecdh_key_size))

    send_video(s, aes_key)
    s.close()

if __name__ == "__main__":
    main()
