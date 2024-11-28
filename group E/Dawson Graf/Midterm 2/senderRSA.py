import cv2
import socket
import pickle
import numpy as np
from os import urandom
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from picamera2 import Picamera2
import time

server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
server_public_key = server_key.public_key()
server_public_key_bytes = server_public_key.public_bytes(
    encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
)

host, port = "0.0.0.0", 5000
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(1)
conn, addr = server_socket.accept()
conn.sendall(server_public_key_bytes)
client_public_key = serialization.load_pem_public_key(conn.recv(4096))

start_dh = time.time()
client_random_value = server_key.decrypt(
    conn.recv(256), OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)
server_random_value = urandom(32)
conn.sendall(client_public_key.encrypt(
    server_random_value, OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
))
shared_secret = HKDF(
    algorithm=hashes.SHA256(), length=32, salt=None, info=b'shared secret'
).derive(client_random_value + server_random_value)
end_dh = time.time()

iv = urandom(16)
cipher = Cipher(algorithms.AES(shared_secret), modes.CFB(iv))
encryptor = cipher.encryptor()
conn.sendall(iv)

camera = Picamera2()
camera.configure(camera.create_video_configuration(main={"size": (640, 480)}))
camera.start()

frame_count = 0
total_encryption_time = 0
total_bandwidth = 0
start_stream_time = time.time()

try:
    while True:
        video_frame = cv2.cvtColor(camera.capture_array(), cv2.COLOR_BGR2RGB)
        frame_data = pickle.dumps(cv2.resize(video_frame, (640, 480)))
        start_encryption = time.time()
        encrypted_frame = encryptor.update(frame_data)
        end_encryption = time.time()
        total_encryption_time += end_encryption - start_encryption
        payload = pickle.dumps(encrypted_frame)
        frame_size = len(payload)
        total_bandwidth += frame_size
        conn.sendall(frame_size.to_bytes(4, 'big') + payload)

        encrypted_display = np.frombuffer(encrypted_frame, dtype=np.uint8)[:640 * 480].reshape((480, 640))
        cv2.imshow("Encrypted Video", encrypted_display)
        frame_count += 1

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
except:
    pass

end_stream_time = time.time()
total_stream_time = end_stream_time - start_stream_time
average_bandwidth = total_bandwidth / total_stream_time

print(f"\n[Metrics]")
print(f"Diffie-Hellman Execution Time: {end_dh - start_dh:.6f} seconds")
print(f"Total Encryption Time: {total_encryption_time:.6f} seconds")
print(f"Total Bandwidth Used: {total_bandwidth / 1_000_000:.2f} MB")
print(f"Average Bandwidth Usage: {average_bandwidth / 1_000:.2f} KB/s")
print(f"Total Streaming Time: {total_stream_time:.2f} seconds")

camera.stop()
conn.close()
server_socket.close()
cv2.destroyAllWindows()
