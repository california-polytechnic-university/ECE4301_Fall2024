import socket
import struct
import time
import cv2
from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes

# Set up socket for sending video
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(0)

# Accept a single connection
connection = server_socket.accept()[0].makefile('wb')

# Initialize USB webcam
cap = cv2.VideoCapture(0)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Generate key and nonce for ChaCha20
key = get_random_bytes(32)
nonce = get_random_bytes(12)

# Send key and nonce to the client
connection.write(key)
connection.write(nonce)
connection.flush()

# Send frame dimensions
connection.write(struct.pack('<LL', frame_width, frame_height))
connection.flush()

# Start capturing video
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Display the frame
        cv2.imshow('Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Convert frame to bytes
        frame_data = frame.tobytes()

        # Measure encryption time
        start_time = time.time()
        cipher = ChaCha20.new(key=key, nonce=nonce)
        encrypted_frame = cipher.encrypt(frame_data)
        encryption_time = time.time() - start_time
        print(f"Encryption time: {encryption_time:.6f} seconds")

        # Send the length of the encrypted frame
        connection.write(struct.pack('<L', len(encrypted_frame)))
        connection.flush()

        # Send the encrypted frame
        connection.write(encrypted_frame)
        connection.flush()
finally:
    cap.release()
    connection.close()
    server_socket.close()
    cv2.destroyAllWindows()
