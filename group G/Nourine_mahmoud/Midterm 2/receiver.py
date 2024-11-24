import socket
import cv2
import numpy as np
import random
import os
import time
from hashlib import sha256

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import serialization

def main():
    # Generate receiver's RSA key pair
    print("Generating receiver's RSA key pair...")
    receiver_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    receiver_public_key = receiver_private_key.public_key()
    print("Receiver's RSA key pair generated.")

    # Serialize receiver's public key to send to the sender
    receiver_public_key_pem = receiver_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Set up server socket
    HOST = '0.0.0.0'
    PORT = 6001
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((HOST, PORT))
    server_sock.listen(1)
    print('Waiting for connection from sender...')

    conn, addr = server_sock.accept()
    print(f'Connected by {addr}')

    # Send receiver's public key to the sender
    conn.sendall(receiver_public_key_pem)
    print('Sent receiver\'s public RSA public key to sender.')

    # Receive sender's public RSA key
    print("Receiving sender's RSA public key...")
    sender_public_key_pem = b''
    while True:
        data = conn.recv(4096)
        if not data:
            break
        sender_public_key_pem += data
        if b'-----END PUBLIC KEY-----' in sender_public_key_pem:
            break

    sender_public_key = serialization.load_pem_public_key(sender_public_key_pem)
    print("Received sender's RSA public key.")

    # -------------------------
    # Diffie-Hellman Key Exchange with RSA Signatures
    # -------------------------

    print("Performing Diffie-Hellman key exchange with RSA signatures...")

    # Standard Diffie-Hellman parameters
    p_hex = """
    FFFFFFFFFFFFFFFFADf85458A2BB4A9AAFDC5620273D3CF1
    D8B9C583CE2D3695A9E1364114644699E6A72019
    """.replace("\n", "").replace(" ", "")
    p = int(p_hex, 16)
    g = 2
    print(f"Using standard Diffie-Hellman parameters:\n p = {p}\n g = {g}")

    # Receiver's private and public values
    b = random.randint(2, p - 2)
    B = pow(g, b, p)
    print(f"Receiver's private key (b) generated.")
    print(f"Receiver's public value (B) computed.")

    # Receive A and signature from sender
    print("Receiving A and signature from sender...")
    # Receive A
    A_length_bytes = conn.recv(4)
    if not A_length_bytes:
        print("Failed to receive A length.")
        return
    A_length = int.from_bytes(A_length_bytes, 'big')
    A_bytes = b''
    while len(A_bytes) < A_length:
        packet = conn.recv(A_length - len(A_bytes))
        if not packet:
            print("Failed to receive A.")
            return
        A_bytes += packet
    A = int.from_bytes(A_bytes, 'big')
    print(f"Received A from sender: {A}")

    # Receive signature
    signature_length_bytes = conn.recv(4)
    if not signature_length_bytes:
        print("Failed to receive signature length.")
        return
    signature_length = int.from_bytes(signature_length_bytes, 'big')
    signature = b''
    while len(signature) < signature_length:
        packet = conn.recv(signature_length - len(signature))
        if not packet:
            print("Failed to receive signature.")
            return
        signature += packet
    print("Received signature from sender.")

    # Verify signature using sender's public RSA key
    try:
        sender_public_key.verify(
            signature,
            A_bytes,
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        print("Sender's signature verified successfully.")
    except Exception as e:
        print(f"Signature verification failed: {e}")
        return

    # Serialize public key B
    B_bytes = B.to_bytes((B.bit_length() + 7) // 8, 'big')

    # Sign B using receiver's RSA private key
    signature = receiver_private_key.sign(
        B_bytes,
        asym_padding.PSS(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            salt_length=asym_padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    print("Receiver's public value (B) signed.")

    # Send B and signature to sender
    conn.sendall(len(B_bytes).to_bytes(4, 'big') + B_bytes)
    conn.sendall(len(signature).to_bytes(4, 'big') + signature)
    print("Sent B and signature to sender.")

    # Compute shared secret
    shared_secret = pow(A, b, p)
    print(f"Computed shared secret.")

    # Derive AES key from shared secret
    aes_key = sha256(str(shared_secret).encode()).digest()
    print("AES key established.")

    # Mode of security packets (AES in CBC mode)
    security_mode = "AES-256 in CBC mode with PKCS7 padding"
    print(f"Security mode: {security_mode}")

    # Prepare to receive and display video frames
    WIDTH, HEIGHT = 640, 480

    print("Ready to receive and decrypt video frames.")

    i = 0
    
    try:
        while True:
            # Start time for receiving frame
            receive_start_time = time.time()

            # Read message length (first 4 bytes)
            length_bytes = conn.recv(4)
            if not length_bytes:
                print("No data received. Closing connection.")
                break
            message_length = int.from_bytes(length_bytes, 'big')

            # Receive the full message
            data = b''
            while len(data) < message_length:
                packet = conn.recv(message_length - len(data))
                if not packet:
                    print("Connection lost during frame reception.")
                    break
                data += packet

            receive_end_time = time.time()
            receive_time = (receive_end_time - receive_start_time) * 1000  # Convert to milliseconds
            

            if len(data) != message_length:
                print("Incomplete data received. Skipping frame.")
                continue

            # Extract IV and ciphertext
            iv, ciphertext = data[:16], data[16:]

            # Start time for decryption
            decryption_start_time = time.time()

            # Decrypt the frame
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded_frame_bytes = decryptor.update(ciphertext) + decryptor.finalize()

            # Remove PKCS7 padding
            unpadder = padding.PKCS7(128).unpadder()
            try:
                frame_bytes = unpadder.update(padded_frame_bytes) + unpadder.finalize()
            except ValueError as e:
                print(f"Unpadding error: {e}")
                continue

            # End time for decryption
            decryption_end_time = time.time()
            decryption_time = (decryption_end_time - decryption_start_time) * 1000  # Convert to milliseconds
            if i < 10:
                print(f"Frame decrypted in {decryption_time:.2f} ms.")
                print(f"Frame received in {receive_time:.2f} ms.")
                i += 1

            # Convert bytes back to image
            try:
                frame = np.frombuffer(frame_bytes, dtype=np.uint8).reshape(HEIGHT, WIDTH, 4)
            except ValueError as e:
                print(f"Error reshaping frame: {e}")
                continue

            # Display the frame
            cv2.imshow("Decrypted Video Stream", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Exiting video stream.")
                break
    except KeyboardInterrupt:
        print("Stream stopped by user.")
    finally:
        conn.close()
        server_sock.close()
        cv2.destroyAllWindows()
        print("Connection closed and resources released.")

if __name__ == '__main__':
    main()
