import cv2
import socket
import struct
from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes
from picamera2 import Picamera2
import numpy as np

# Initialize the camera
camera = Picamera2()
camera_config = camera.create_video_configuration(main={"size": (640, 360)})
camera.configure(camera_config)
camera.start()

# Set up the network socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 5000))
server.listen(1)
print("Waiting for a connection on port 5000...")

# Accept connection from the client
client_socket, client_address = server.accept()
print(f"Connected to: {client_address}")

# Generate a unique encryption key and nonce for ChaCha20
encryption_key = get_random_bytes(32)
encryption_nonce = get_random_bytes(12)

# Share encryption key and frame dimensions with the client
client_socket.sendall(encryption_key)
client_socket.sendall(encryption_nonce)
client_socket.sendall(struct.pack('<L', 640))  # Send width
client_socket.sendall(struct.pack('<L', 360))  # Send height

# Function to render encrypted data as a visual representation
def render_encrypted_frame(data, width, height):
    max_pixels = width * height
    processed_data = np.frombuffer(data[:max_pixels], dtype=np.uint8)
    padded_data = np.pad(processed_data, (0, max_pixels - len(processed_data)), mode='constant')
    return padded_data.reshape((height, width))

# Main streaming loop
try:
    while True:
        # Capture a frame from the camera
        video_frame = camera.capture_array()

        # Compress the frame into JPEG format
        success, compressed_frame = cv2.imencode('.jpg', video_frame)

        # Encrypt the compressed frame
        cipher = ChaCha20.new(key=encryption_key, nonce=encryption_nonce)
        encrypted_data = cipher.encrypt(compressed_frame.tobytes())

        # Send the encrypted frame to the client
        frame_size = struct.pack('<L', len(encrypted_data))
        client_socket.sendall(frame_size + encrypted_data)

        # Visualize the encrypted frame locally
        encrypted_display = render_encrypted_frame(encrypted_data, 640, 360)
        cv2.imshow('Encrypted Video Display', encrypted_display)

        # Exit when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
except Exception as error:
    print(f"An error occurred: {error}")
finally:
    camera.stop()
    client_socket.close()
    server.close()
    cv2.destroyAllWindows()
