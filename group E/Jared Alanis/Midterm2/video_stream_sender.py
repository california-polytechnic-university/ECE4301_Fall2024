import cv2
import socket
import pickle
import time
from time import perf_counter_ns
from cryptography.fernet import Fernet

# TCP Socket setup
HOST = '192.168.1.207'  # Replace with receiver's IP
PORT = 12345
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

# Start Diffie-Hellman execution
dh_start = perf_counter_ns()

# Generate a Fernet key and send it to the receiver
key = Fernet.generate_key()
sock.sendall(key)
cipher = Fernet(key)

dh_end = perf_counter_ns()
diffie_hellman_time_ns = dh_end - dh_start

print(f"Shared key established. Diffie-Hellman Execution Time: {diffie_hellman_time_ns / 1_000_000:.3f} milliseconds")

# Initialize the camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# Metrics
frame_count = 0
total_encryption_time = 0
total_transmission_time = 0
start_time = perf_counter_ns()

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture video.")
            break

        # Serialize the frame
        frame_data = pickle.dumps(frame)

        # Measure encryption time
        encryption_start = perf_counter_ns()
        encrypted_frame = cipher.encrypt(frame_data)
        encryption_end = perf_counter_ns()
        encryption_time = (encryption_end - encryption_start) / 1_000_000  # Convert to milliseconds
        total_encryption_time += encryption_time

        # Measure transmission time
        frame_size = len(encrypted_frame)
        transmission_start = perf_counter_ns()
        sock.sendall(frame_size.to_bytes(4, 'big') + encrypted_frame)
        transmission_end = perf_counter_ns()
        transmission_time = (transmission_end - transmission_start) / 1_000_000  # Convert to milliseconds
        total_transmission_time += transmission_time

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
            f"Enc Time: {encryption_time:.2f} ms",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            1,
        )
        cv2.putText(
            frame,
            f"Trans Time: {transmission_time:.2f} ms",
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            1,
        )

        # Display the video locally on the sender
        cv2.imshow('Video on Sender (PBox)', frame)

        # Increment frame count
        frame_count += 1

        # Quit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print(f"Error: {e}")
finally:
    # Calculate metrics
    total_time = (perf_counter_ns() - start_time) / 1_000_000_000  # Convert to seconds
    average_encryption_time = total_encryption_time / frame_count if frame_count > 0 else 0
    average_transmission_time = total_transmission_time / frame_count if frame_count > 0 else 0
    average_frame_rate = frame_count / total_time if total_time > 0 else 0

    print(f"\n[Metrics]")
    print(f"Diffie-Hellman Execution Time: {diffie_hellman_time_ns / 1_000_000:.3f} milliseconds")
    print(f"Total Frames Sent: {frame_count}")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Average Encryption Time: {average_encryption_time:.2f} ms/frame")
    print(f"Average Transmission Time: {average_transmission_time:.2f} ms/frame")
    print(f"Average Frame Rate: {average_frame_rate:.2f} FPS")

    # Cleanup
    cap.release()
    sock.close()
    cv2.destroyAllWindows()
