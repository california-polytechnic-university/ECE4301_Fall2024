# receiver.py
import cv2
import socket
import struct
import threading
import numpy as np
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding as asym_padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
import time

# Choose AES mode (CBC, CFB, GCM)
AES_MODE = AES.MODE_CBC  # You can change this to AES.MODE_CFB, AES.MODE_GCM, etc.

# Variables for performance metrics
key_exchange_time = 0
packet_transmission_times = []
ecdh_key_size = 0

def key_exchange(conn):
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

        # Receive RPI's RSA public key
        rpi_public_key_length = struct.unpack('!I', conn.recv(4))[0]
        rpi_public_key_pem = conn.recv(rpi_public_key_length)
        rpi_public_key = serialization.load_pem_public_key(
            rpi_public_key_pem,
            backend=default_backend()
        )

        # Send PC's RSA public key
        pc_public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        conn.sendall(struct.pack('!I', len(pc_public_key_pem)))
        conn.sendall(pc_public_key_pem)

        # Generate ECDH private key
        pc_private_key_ecdh = ec.generate_private_key(ec.SECP256R1(), backend=default_backend())
        pc_public_key_ecdh = pc_private_key_ecdh.public_key()

        # Serialize ECDH public key
        pc_public_key_ecdh_bytes = pc_public_key_ecdh.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        ecdh_key_size = len(pc_public_key_ecdh_bytes) * 8  # in bits

        # Receive and decrypt RPI's ECDH public key
        encrypted_rpi_public_key_length = struct.unpack('!I', conn.recv(4))[0]
        encrypted_rpi_public_key_ecdh = conn.recv(encrypted_rpi_public_key_length)
        rpi_public_key_ecdh_bytes = private_key.decrypt(
            encrypted_rpi_public_key_ecdh,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        rpi_public_key_ecdh = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), rpi_public_key_ecdh_bytes)

        # Encrypt and send PC's ECDH public key
        encrypted_pc_public_key_ecdh = rpi_public_key.encrypt(
            pc_public_key_ecdh_bytes,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        conn.sendall(struct.pack('!I', len(encrypted_pc_public_key_ecdh)))
        conn.sendall(encrypted_pc_public_key_ecdh)

        # Generate shared secret
        shared_key = pc_private_key_ecdh.exchange(ec.ECDH(), rpi_public_key_ecdh)

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
        conn.close()
        exit(1)

def receive_video(conn, aes_key):
    frame_count = 0
    # Receive ECDH key size from Raspberry Pi
    global ecdh_key_size
    ecdh_key_size = struct.unpack('!I', conn.recv(4))[0]

    try:
        while True:
            start_time = time.time()
            # Receive data length
            data_length_bytes = conn.recv(4)
            if not data_length_bytes:
                break
            data_length = struct.unpack('!I', data_length_bytes)[0]

            # Receive data
            data = b''
            while len(data) < data_length:
                packet = conn.recv(data_length - len(data))
                if not packet:
                    break
                data += packet

            if not data:
                break

            # Separate IV and ciphertext
            iv = data[:16]
            ciphertext = data[16:]

            # AES Decryption
            cipher = AES.new(aes_key, AES_MODE, iv)
            frame_bytes_padded = cipher.decrypt(ciphertext)
            frame_bytes = unpad(frame_bytes_padded, AES.block_size)

            # Decode frame
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            end_time = time.time()
            transmission_time = end_time - start_time
            packet_transmission_times.append(transmission_time)
            frame_count += 1

            # Display performance metrics on the frame
            if frame is not None:
                metrics_text = (f"Key Exchange Time: {key_exchange_time:.4f}s\n"
                                f"Avg Packet Time: {sum(packet_transmission_times[-30:]) / min(30, len(packet_transmission_times)):.4f}s\n"
                                f"EC Key Size: {ecdh_key_size} bits")
                y0, dy = 30, 30
                for i, line in enumerate(metrics_text.split('\n')):
                    y = y0 + i * dy
                    cv2.putText(frame, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                cv2.imshow('Decrypted Video', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        print("Video stream ended")
    except Exception as e:
        print("Error during video reception: ", e)
    finally:
        conn.close()
        cv2.destroyAllWindows()

def main():
    HOST = ''
    PORT = 65432

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print("Waiting for connection from Raspberry Pi...")
    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")

    aes_key = key_exchange(conn)
    receive_video(conn, aes_key)

if __name__ == "__main__":
    main()
