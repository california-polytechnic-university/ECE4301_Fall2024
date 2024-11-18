import cv2
import socket
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.backends import default_backend
import struct
import time

# Function to apply ChaCha20 encryption
def encrypt_file(key, filename):
    nonce = os.urandom(16)  # Generate a new nonce for encryption
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
    encryptor = cipher.encryptor()

    # Encrypt the file
    with open(filename, 'rb') as f:
        plaintext = f.read()
        encrypted_data = encryptor.update(plaintext) + encryptor.finalize()

    return nonce, encrypted_data

# Initialize socket connection (Raspberry Pi acting as the client)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.1.213', 1900))  # Replace with the PC's IP address

# ChaCha20 key (32 bytes)
key = b'This_is_a_32_byte_long_key!!_abc'

# Open the webcam and set up the video writer
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Capture the actual frame rate of the webcam
fps_cam = cap.get(cv2.CAP_PROP_FPS)
print(f"Camera FPS: {fps_cam}")

# Use the captured FPS if available, or default to 15.0 FPS
fps = fps_cam if fps_cam > 0 else 15.0

# Output video file name
video_filename = 'Recorded_Video.avi'
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(video_filename, fourcc, fps, (640, 480))

print("Press 'q' to stop recording...")

# Record video until 'q' is pressed
start_time = time.time()  # Record the start time
frame_count = 0  # To count frames
while True:
    ret, frame = cap.read()
    if ret:
        out.write(frame)
        cv2.imshow('Recording', frame)
        frame_count += 1
        time.sleep(1/fps)  # Ensure the frame rate is followed
    else:
        break

    # Check for key press to stop recording
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release video capture and writer
out.release()
cap.release()
cv2.destroyAllWindows()

end_time = time.time()
total_recording_time = end_time - start_time - 1.0

# Encrypt the recorded video
start_encryption_time = time.time()  # Start time for encryption
nonce, encrypted_data = encrypt_file(key, video_filename)
end_encryption_time = time.time()  # End time for encryption
total_encryption_time = end_encryption_time - start_encryption_time 

# Send the encrypted video to the server
start_transmission_time = time.time()  # Start time for transmission

# Send the nonce (16 bytes)
client_socket.sendall(nonce)

# Send the length of the encrypted data
client_socket.sendall(struct.pack("Q", len(encrypted_data)))

# Send the encrypted video data
client_socket.sendall(encrypted_data)

end_transmission_time = time.time()  # End time for transmission
total_transmission_time = end_transmission_time - start_transmission_time

# Close the socket connection
client_socket.close()

print(f"Sent encrypted video '{video_filename}' to the PC.")

# Present performance metrics
print(f"\nPerformance Metrics:")
print(f"Total recorded time: {total_recording_time:.2f} seconds")
print(f"Frames recorded: {frame_count}")
print(f"Actual FPS: {frame_count / total_recording_time:.2f} frames per second")
print(f"Encryption time: {total_encryption_time:.2f} seconds")
print(f"Transmission time: {total_transmission_time:.2f} seconds")
