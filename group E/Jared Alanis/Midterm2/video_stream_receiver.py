import cv2
import socket
import pickle
import time
from time import perf_counter_ns
from cryptography.fernet import Fernet

# TCP Socket setup
HOST = '0.0.0.0'
PORT = 12345
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(1)

print("Waiting for connection...")
conn, addr = sock.accept()
print(f"Connected by {addr}")

# Start Diffie-Hellman execution
dh_start = perf_counter_ns()

# Receive the Fernet key
key = conn.recv(44)  # Fernet keys are always 44 bytes
cipher = Fernet(key)

dh_end = perf_counter_ns()
diffie_hellman_time_ns = dh_end - dh_start

print(f"Shared key established. Diffie-Hellman Execution Time: {diffie_hellman_time_ns / 1_000_000:.3f} milliseconds")

# Metrics
frame_count = 0
total_decryption_time = 0
start_time = perf_counter_ns()

# Helper function to read exact bytes
def read_exact_bytes(conn, num_bytes):
    data = b''
    while len(data) < num_bytes:
        chunk = conn.recv(num_bytes - len(data))
        if not chunk:
            raise ConnectionError("Connection closed while receiving data.")
        data += chunk
    return data

try:
    while True:
        # Read the 4-byte frame size
        frame_size_bytes = read_exact_bytes(conn, 4)
        frame_size = int.from_bytes(frame_size_bytes, 'big')

        # Read the encrypted frame
        encrypted_frame = read_exact_bytes(conn, frame_size)

        # Measure decryption time
        decryption_start = perf_counter_ns()
        decrypted_frame_data = cipher.decrypt(encrypted_frame)
        decryption_end = perf_counter_ns()
        decryption_time = (decryption_end - decryption_start) / 1_000_000  # Convert to milliseconds
        total_decryption_time += decryption_time

        # Deserialize the frame
        frame = pickle.loads(decrypted_frame_data)

        # Display metrics in a Performance Box (PBox) on the video
        elapsed_time = (perf_counter_ns() - start_time) / 1_000_000_000  # Convert to seconds
        cv2.putText(
            frame,
            f"FPS: {frame_count / elapsed_time:.2f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            1,
        )
        cv2.putText(
            frame,
            f"Dec Time: {decryption_time:.2f} ms",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            1,
        )

        # Display the video
        cv2.imshow('Video on Receiver (PBox)', frame)

        # Increment frame count
        frame_count += 1

        # Quit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except ConnectionError as e:
    print(f"Connection error: {e}")
except Exception as e:
    print(f"Error: {e}")
finally:
    # Calculate metrics
    total_time = (perf_counter_ns() - start_time) / 1_000_000_000  # Convert to seconds
    average_decryption_time = total_decryption_time / frame_count if frame_count > 0 else 0
    average_frame_rate = frame_count / total_time if total_time > 0 else 0

    print(f"\n[Metrics]")
    print(f"Diffie-Hellman Execution Time: {diffie_hellman_time_ns / 1_000_000:.3f} milliseconds")
    print(f"Total Frames Received: {frame_count}")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Average Decryption Time: {average_decryption_time:.2f} ms/frame")
    print(f"Average Frame Rate: {average_frame_rate:.2f} FPS")

    # Cleanup
    conn.close()
    sock.close()
    cv2.destroyAllWindows()
