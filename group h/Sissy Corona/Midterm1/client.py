import socket
import cv2
import numpy as np
from Cryptobytes.Cipher import ChaCha20

# Set up the client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.bind(('127.0.0.1', 5000))

# Create ChaCha20 cipher object for decryption
cipher = ChaCha20.new(key=key, nonce=nonce)

while True:
    # Receive encrypted frame data
    encrypted_frame_data, _ = client_socket.recvfrom(65536)

    # Decrypt the frame data
    decrypted_frame_data = cipher.decrypt(encrypted_frame_data)

    # Decode the frame back to a usable format (JPEG -> image)
    frame = cv2.imdecode(np.frombuffer(decrypted_frame_data, dtype=np.uint8), 1)

    # Display the resulting frame
    if frame is not None:
        cv2.imshow('Decrypted Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, close the window and socket
cv2.destroyAllWindows()
client_socket.close()
