import socket, cv2, time, numpy as np
from Crypto.Cipher import ChaCha20_Poly1305
from Crypto.Random import get_random_bytes
import rpi_config  # Import the configuration file

# Function to encrypt data using ChaCha20-Poly1305
def encrypt_chacha20(key, nonce, data):
    cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return ciphertext, tag

# Set up the socket client
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((rpi_config.WINDOWS_HOST_IP, rpi_config.PORT))  # Use variables from rpi_config

# Generate key and nonce
key = get_random_bytes(32)
nonce = get_random_bytes(12)

# Send key and nonce to the Windows host
client_socket.sendall(key)
client_socket.sendall(nonce)

# Capture video from the Raspberry Pi camera
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Convert frame to bytes
    frame_bytes = frame.tobytes()

    # Encrypt the frame and measure the time taken
    start_time = time.time()
    encrypted_frame_bytes, tag = encrypt_chacha20(key, nonce, frame_bytes)
    encryption_time = time.time() - start_time

    # Send the encrypted frame and tag
    client_socket.sendall(encrypted_frame_bytes + tag)

    # Display the raw frame with a caption
    cv2.putText(frame, 'Raw Webcam Feed', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imshow('Raw Frame', frame)

    # Convert the encrypted frame bytes back to an image for display
    encrypted_frame = np.frombuffer(encrypted_frame_bytes, dtype=np.uint8).reshape((480, 640, 3))  # Adjust the shape as needed

    # Add caption to the encrypted frame
    caption = f'Encrypted Frame - Time: {encryption_time:.4f}s'
    cv2.putText(encrypted_frame, caption, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imshow('Encrypted Frame', encrypted_frame)

    if cv2.waitKey(1) & 0xFF == 27:  # Escape key
        break

# Release the capture and close the socket
cap.release()
client_socket.close()
cv2.destroyAllWindows()