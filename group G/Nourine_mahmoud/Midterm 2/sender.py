import socket
from picamera2 import Picamera2
import numpy as np
import random
import os
import time
from hashlib import sha256
import cv2  # Import OpenCV for video display

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import serialization

def main():
    # Generate sender's RSA key pair
    sender_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    sender_public_key = sender_private_key.public_key()

    # Set up socket
    HOST = '192.168.1.16'  # Replace with receiver's IP address
    PORT = 6001
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("Connecting to receiver...")
    sock.connect((HOST, PORT))
    print("Connected successfully!")

    # Receive receiver's public RSA key
    recv_public_key_pem = b''
    while True:
        data = sock.recv(4096)
        if not data:
            break
        recv_public_key_pem += data
        if b'-----END PUBLIC KEY-----' in recv_public_key_pem:
            break

    receiver_public_key = serialization.load_pem_public_key(recv_public_key_pem)
    print("Received receiver's public key.")

    # Send sender's public RSA key to receiver
    sender_public_key_pem = sender_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    sock.sendall(sender_public_key_pem)
    print("Sent sender's public key to receiver.")

    # -------------------------
    # Diffie-Hellman Key Exchange with RSA Signatures
    # -------------------------

    print("Performing Diffie-Hellman key exchange with RSA signatures...")
    start_time_dh = time.perf_counter()  # Start timing Diffie-Hellman execution

    # Standard Diffie-Hellman parameters
    p_hex = """
    FFFFFFFFFFFFFFFFADf85458A2BB4A9AAFDC5620273D3CF1
    D8B9C583CE2D3695A9E1364114644699E6A72019
    """.replace("\n", "").replace(" ", "")
    p = int(p_hex, 16)
    g = 2

    # Sender's private and public values
    a = random.randint(2, p - 2)
    A = pow(g, a, p)

    # Serialize public key A
    A_bytes = A.to_bytes((A.bit_length() + 7) // 8, 'big')

    # Sign A using sender's RSA private key
    signature = sender_private_key.sign(
        A_bytes,
        asym_padding.PSS(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            salt_length=asym_padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    # Send A and signature to receiver
    sock.sendall(len(A_bytes).to_bytes(4, 'big') + A_bytes)
    sock.sendall(len(signature).to_bytes(4, 'big') + signature)
    print("Sent A and signature to receiver.")

    # Receive B and signature from receiver
    # Receive B
    B_length_bytes = sock.recv(4)
    B_length = int.from_bytes(B_length_bytes, 'big')
    B_bytes = sock.recv(B_length)
    B = int.from_bytes(B_bytes, 'big')

    # Receive signature
    signature_length_bytes = sock.recv(4)
    signature_length = int.from_bytes(signature_length_bytes, 'big')
    signature = sock.recv(signature_length)

    # Verify signature using receiver's public RSA key
    receiver_public_key.verify(
        signature,
        B_bytes,
        asym_padding.PSS(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            salt_length=asym_padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    print("Verified receiver's signature.")

    # Compute shared secret
    shared_secret = pow(B, a, p)

    # Derive AES key from shared secret
    aes_key = sha256(str(shared_secret).encode()).digest()
    print("AES key established.")

    end_time_dh = time.perf_counter()  # End timing Diffie-Hellman execution
    dh_execution_time = end_time_dh - start_time_dh
    print(f"Diffie-Hellman key exchange took {dh_execution_time:.6f} seconds.")

    # Mode of security packets (AES in CBC mode)
    security_mode = "AES-256 in CBC mode with PKCS7 padding"
    print(f"Security mode: {security_mode}")
    
    # Initialize camera
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (640, 480)})  # Ensure resolution is 640x480
    picam2.configure(config)
    picam2.start()

    print("Streaming encrypted camera feed...")


    i = 0
    try:
        while True:
            start_time_packet = time.perf_counter()  # Start timing packet execution

            # Capture a frame
            frame = picam2.capture_array()

            # Display the frame before encryption
            cv2.imshow('Sender Video Feed', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Convert frame to bytes
            frame_bytes = frame.tobytes()

            # Pad the frame to a multiple of 16 bytes
            padder = padding.PKCS7(128).padder()
            padded_frame = padder.update(frame_bytes) + padder.finalize()

            # Generate a unique IV for this frame
            iv = os.urandom(16)

            # Encrypt the frame
            start_time_encrypt = time.perf_counter()  # Start timing encryption
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded_frame) + encryptor.finalize()
            end_time_encrypt = time.perf_counter()  # End timing encryption
            encryption_time = end_time_encrypt - start_time_encrypt
            

            # Create message: IV + Ciphertext
            message = iv + ciphertext
            message_length = len(message)

            # Send message length followed by message
            sock.sendall(message_length.to_bytes(4, 'big') + message)

            end_time_packet = time.perf_counter()  # End timing packet execution
            packet_execution_time = end_time_packet - start_time_packet
            if i < 10:
                print(f"Encryption time: {encryption_time:.6f} seconds.")
                print(f"Packet execution time: {packet_execution_time:.6f} seconds.")
                i+=1

            # Limit frame rate to 30 FPS
            time.sleep(0.033)
    except KeyboardInterrupt:
        print("Stream stopped.")
    finally:
        sock.close()
        picam2.stop()
        cv2.destroyAllWindows()  # Close the OpenCV window

if __name__ == "__main__":
    main()
