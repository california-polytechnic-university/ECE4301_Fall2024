import cv2
import socket
import struct
import numpy as np
from Crypto.Cipher import ChaCha20

# Initialize the socket for receiving encrypted video
receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receiver_socket.connect(('192.168.1.133', 5000))  # Replace with the Raspberry Pi's IP address

# Retrieve the encryption key and nonce from the server
encryption_key = receiver_socket.recv(32)
encryption_nonce = receiver_socket.recv(12)
print("Encryption key and nonce received from the server.")

# Receive the video resolution (width and height)
video_width, video_height = struct.unpack('<LL', receiver_socket.recv(8))
print(f"Video resolution received: {video_width}x{video_height}")

# Buffer for incoming encrypted video data
incoming_data = b''

# Main loop to receive, decrypt, and display video frames
try:
    while True:
        # Receive the size of the incoming frame
        size_packet = receiver_socket.recv(4)
        if not size_packet:
            print("Connection closed by the server.")
            break

        frame_size = struct.unpack('<L', size_packet)[0]

        # Receive the encrypted frame
        while len(incoming_data) < frame_size:
            incoming_data += receiver_socket.recv(frame_size - len(incoming_data))

        encrypted_video = incoming_data[:frame_size]
        incoming_data = incoming_data[frame_size:]

        # Decrypt the frame using ChaCha20
        decryption_cipher = ChaCha20.new(key=encryption_key, nonce=encryption_nonce)
        decrypted_data = decryption_cipher.decrypt(encrypted_video)

        # Decode the decrypted data back into an image
        image_buffer = np.frombuffer(decrypted_data, dtype=np.uint8)
        frame_image = cv2.imdecode(image_buffer, cv2.IMREAD_COLOR)

        # Display the decrypted video frame
        cv2.imshow('Decrypted Video Feed', frame_image)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting video stream.")
            break
except Exception as error:
    print(f"An error occurred: {error}")
finally:
    receiver_socket.close()
    cv2.destroyAllWindows()
