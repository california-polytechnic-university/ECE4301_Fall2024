import socket
import cv2
import numpy as np
import time
from Crypto.Cipher import ChaCha20

# Set up the client socket (TCP)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.1.131', 5000))  # Use connect() for TCP

key = bytes.fromhex('4f37dbc1dbe191a63aaf9d115f512d7a80119da8f3479250e3c4497264800ad8')
nonce = bytes.fromhex('8f8ca8239e2bccd22a1334ba')  

# Create ChaCha20 cipher object for decryption
cipher = ChaCha20.new(key=key, nonce=nonce)

while True:
    encrypted_frame_data = client_socket.recv(65536)
    print(f"Encrypted frame size: {len(encrypted_frame_data)} bytes")

    # Start measuring decryption time
    start_time = time.time()

    # Decrypt the frame data
    decrypted_frame_data = cipher.decrypt(encrypted_frame_data)
    print(f"Decrypted data length: {len(decrypted_frame_data)} bytes")

    # Decode the frame back to a usable format (JPEG -> image)
    decrypted_frame = cv2.imdecode(np.frombuffer(decrypted_frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
        
    # Check if the frame is valid
    if decrypted_frame is None:
        print("\n")
    else:
        print("Decrypted frame successfully decoded!")
        cv2.imshow("Decrypted Video Stream", decrypted_frame)

    # Calculate decryption time
    decryption_time = time.time() - start_time
    print(f"Frame decrypted in {decryption_time:.6f} seconds")
    # Check for 'q' key press to break the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, close the windows and socket
cv2.destroyAllWindows()
client_socket.close()
