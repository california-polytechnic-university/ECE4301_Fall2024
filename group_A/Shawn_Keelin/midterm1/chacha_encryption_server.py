import cv2
import socket
import struct
from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes

# Path to your video file
video_file = 'Telescope Drone Hardware Demo Video.mp4'

# Set up video capture from the file
cap = cv2.VideoCapture(video_file)

# Get video dimensions
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

target_width = 640
target_height = 360

# Set up socket for streaming video
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(0)
print("Server listening on port 8000...")

# Wait for a client connection
connection, client_address = server_socket.accept()
print("Connection established with: ", client_address)

# Generate a random 256-bit key and nonce for ChaCha20 encryption
key = get_random_bytes(32)
nonce = get_random_bytes(12)

# Send the key, nonce, width, and height to the client
connection.sendall(key)
connection.sendall(nonce)
connection.sendall(struct.pack('<L', target_width))  # Send width as 4 bytes
connection.sendall(struct.pack('<L', target_height)) # Send height as 4 bytes

# Start streaming the video file
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Downscale the frame to the target resolution (640x360)
    resized_frame = cv2.resize(frame, (target_width, target_height))

    # Compress the frame to JPEG to reduce size
    encoded, buffer = cv2.imencode('.jpg', resized_frame)

    # Encrypt the frame using ChaCha20
    cipher = ChaCha20.new(key=key, nonce=nonce)
    encrypted_frame = cipher.encrypt(buffer.tobytes())

    # Send the length of the encrypted frame followed by the encrypted frame
    frame_length = struct.pack('<L', len(encrypted_frame))
    connection.sendall(frame_length + encrypted_frame)

    # Display the unencrypted frame on the Raspberry Pi (optional)
    cv2.imshow('Unencrypted Frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
connection.close()
server_socket.close()
