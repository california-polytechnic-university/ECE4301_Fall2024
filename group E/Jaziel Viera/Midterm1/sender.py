import socket, cv2, time, numpy as np
from Crypto.Cipher import ChaCha20_Poly1305
from Crypto.Random import get_random_bytes
import rpi5_config  # Import the configuration file

# Function to encrypt data using ChaCha20-Poly1305
def encrypt_chacha20(key, nonce, data):
    cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return ciphertext, tag

# Set up the socket client
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((rpi_config.WINDOWS_HOST_IP, rpi_config.PORT))

# Generate key and nonce
key = get_random_bytes(32)
nonce = get_random_bytes(12)

# Send key and nonce to the Windows host
client_socket.sendall(key)
client_socket.sendall(nonce)

# Capture video from the Raspberry Pi camera
cap = cv2.VideoCapture(0)
frame_size = 480 * 640 * 3  # Adjust if your camera resolution differs

# Variables to track average encryption time
total_encryption_time = 0
frame_count = 0

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Resize to ensure a consistent resolution
        frame = cv2.resize(frame, (640, 480))

        # Convert frame to bytes
        frame_bytes = frame.tobytes()

        # Encrypt the frame and measure the time taken
        start_time = time.time()
        encrypted_frame_bytes, tag = encrypt_chacha20(key, nonce, frame_bytes)
        encryption_time = time.time() - start_time

        # Update encryption time metrics
        total_encryption_time += encryption_time
        frame_count += 1
        avg_encryption_time = total_encryption_time / frame_count

        # Send the encrypted frame and tag
        client_socket.sendall(encrypted_frame_bytes + tag)

        # Display raw frame and encryption metrics
        cv2.imshow('Raw Frame', frame)
        
        # Create a clearer and larger metrics display
        metrics_frame = np.zeros((200, 400, 3), dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(metrics_frame, f'Encryption Time: {encryption_time:.4f}s', (20, 60),
                    font, 0.9, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(metrics_frame, f'Avg Encrypt Time: {avg_encryption_time:.4f}s', (20, 120),
                    font, 0.9, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow('Sender Metrics', metrics_frame)

        if cv2.waitKey(1) & 0xFF == 27:  # Escape key
            break

finally:
    cap.release()
    client_socket.close()
    cv2.destroyAllWindows()
