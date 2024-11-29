import socket
import numpy as np
import cv2
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

cv2.startWindowThread()

# Setup for decryption (ChaCha20)
key = os.urandom(32)  # 256-bit key (must be same as the Raspberry Pi)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP socket
server_ip = '192.168.50.66'  # Replace with the laptop's IP address
server_port = 5001
sock.bind((server_ip, server_port))
sock.listen(1)
print(f"Listening for incoming connection on {server_ip}:{server_port}...")
connection, client_address = sock.accept()
print("Connection established with Raspberry Pi.")

#for i in range(3):
capture = cv2.VideoCapture(0)
    #if capture: break
#Mat frame:

# Function to receive and decrypt the frame
def receive_and_decrypt_frame():
    # Receive the nonce first (16 bytes)
    nonce = connection.recv(16)
    print(f"Received nonce: {nonce.hex()}")  # Debug: Print the received nonce

    # Ensure the nonce length is correct
    if len(nonce) != 16:
        print(f"Error: Expected 16-byte nonce, but received {len(nonce)} bytes.")
        return None

    # Create a new cipher instance with the received nonce
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())

    # Initialize an empty list to store the decrypted data chunks
    decrypted_data = b""

    while True:
        # Receive the encrypted data chunks
        chunk = connection.recv(1024)  # Same chunk size as sent by the Raspberry Pi
        if chunk == b"EOF":  # Check for EOF signal
            print("End of stream reached.")
            break  # End the stream if EOF is received
        if not chunk:
            break  # End of stream or error
        decrypted_data += chunk

    print(f"Total encrypted data size received: {len(decrypted_data)} bytes")  # Debug: Check size of received data

    # Decrypt the data using the ChaCha20 cipher
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(decrypted_data)

    print(f"Total decrypted data size: {len(decrypted_data)} bytes")  # Debug: Size of decrypted data

    # Check if the decrypted data can be properly decoded as a frame
    if len(decrypted_data) < 1000:  # Check if decrypted data is too small to be a valid image
        print("Decrypted data is too small to form a valid frame.")  # Debug: Data size check
        return None

    try:
        nparr = np.frombuffer(decrypted_data, dtype=np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is not None:
            print(f"Decrypted frame shape: {frame.shape}")  # Debug: Frame shape
        else:
            print("Failed to decode frame.")  # Debug: If decoding fails
    except Exception as e:
        print(f"Error decoding frame: {e}")  # Debug error if frame decoding fails

    #return frame

cv2.namedWindow("Decrypted Video")
# Loop to receive and display decrypted video frames
while True:
    ret, frame = capture.read()

    if frame is not None:
        # Display the decrypted frame
        #cv2.namedWindow("Decrypted Video", cv2.WINDOW_AUTOSIZE)
        #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("Decrypted Video", frame)
        cv2.waitKey(10)
    #else:
        #print("Error: Frame is None")

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

#connection.close()
sock.close()
cv2.destroyAllWindows()
