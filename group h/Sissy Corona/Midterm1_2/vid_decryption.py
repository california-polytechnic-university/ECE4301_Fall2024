import cv2
import socket
import ssl
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import pickle
import numpy as np

# Socket setup
HOST = '0.0.0.0'  # Listen on all available interfaces
PORT = 9999
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(1)
print("Waiting for connection...")

# Create an SSL context
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile="server.crt", keyfile="server.key")  # Provide your cert and key files here

# Accept the incoming TLS connection
conn, addr = sock.accept()
tls_conn = context.wrap_socket(conn, server_side=True)  # Use SSLContext's wrap_socket method

print(f"Connected by {addr}")

# Receive key and nonce securely via TLS
metadata = tls_conn.recv(1024)
metadata = pickle.loads(metadata)
key = metadata['key']
nonce = metadata['nonce']

try:
    while True:
        # Receive frame size
        size_data = tls_conn.recv(4)
        if not size_data:
            break
        frame_size = int.from_bytes(size_data, 'big')

        # Receive encrypted frame
        encrypted_frame = tls_conn.recv(frame_size)

        # Decrypt frame
        cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_frame = decryptor.update(encrypted_frame)

        # Decode frame
        frame = cv2.imdecode(np.frombuffer(decrypted_frame, np.uint8), cv2.IMREAD_COLOR)

        # Display frame
        cv2.imshow("Video Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    tls_conn.close()
    sock.close()
    cv2.destroyAllWindows()
