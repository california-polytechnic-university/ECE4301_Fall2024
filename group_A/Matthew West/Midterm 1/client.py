import utils, socket, cv2, time, numpy as np

YOUR_PI_ADDRESS = "127.0.0.1"  # Your Raspberry Pi's IP address

def recv_all(sock, length):
    data = b''
    while len(data) < length:
        packet = sock.recv(length - len(data))
        if not packet:
            raise ConnectionError("Socket connection closed")
        data += packet
    return data

# Generate RSA key pair for the client
t = time.time()
client_n, client_e, client_d = utils.rsa_key_gen()
client_private_rsa_key = (client_n, client_d)
client_rsa_gen_time = time.time() - t

def start_client(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    print(f"Connected to {host}:{port}")
    
    # Receive the host's RSA public key
    t = time.time()
    host_n = int.from_bytes(client_socket.recv(2048), 'big')
    host_e = int.from_bytes(client_socket.recv(2048), 'big')
    host_public_rsa_key = (host_n, host_e)
    host_rsa_gen_time = time.time() - t

    t = time.time()

    # Send the client's RSA public key
    client_socket.sendall(client_n.to_bytes((client_n.bit_length() + 7) // 8, 'big'))
    client_socket.sendall(client_e.to_bytes((client_e.bit_length() + 7) // 8, 'big'))

    # Generate cipher key and nonce
    client_gen_key = utils.gen_key()
    client_gen_nonce = utils.gen_nonce()

    # Encrypt the key and nonce using the host's public key
    encrypted_client_gen_key = utils.encrypt_rsa(client_gen_key, host_public_rsa_key)
    encrypted_client_gen_nonce = utils.encrypt_rsa(client_gen_nonce, host_public_rsa_key)

    # Send the lengths of the encrypted key and nonce
    client_socket.sendall(len(encrypted_client_gen_key).to_bytes(4, 'big'))
    client_socket.sendall(len(encrypted_client_gen_nonce).to_bytes(4, 'big'))

    # Send the encrypted key and nonce to the host
    client_socket.sendall(encrypted_client_gen_key)
    client_socket.sendall(encrypted_client_gen_nonce)

    # Receive the lengths of the encrypted key and nonce from the host
    host_key_length = int.from_bytes(recv_all(client_socket, 4), 'big')
    host_nonce_length = int.from_bytes(recv_all(client_socket, 4), 'big')

    # Receive the encrypted key and nonce from the host
    encrypted_host_gen_key = recv_all(client_socket, host_key_length)
    encrypted_host_gen_nonce = recv_all(client_socket, host_nonce_length)

    # Decrypt the key and nonce using the client's private key
    host_gen_key = utils.decrypt_rsa(encrypted_host_gen_key, client_private_rsa_key)
    host_gen_nonce = utils.decrypt_rsa(encrypted_host_gen_nonce, client_private_rsa_key)

    # Derive the shared secret key and nonce
    ss_key = int.from_bytes(client_gen_key, byteorder='big') ^ int.from_bytes(host_gen_key, byteorder='big')
    ss_nonce = int.from_bytes(client_gen_nonce, byteorder='big') ^ int.from_bytes(host_gen_nonce, byteorder='big')

    # Hash the shared secret key and nonce
    ss_key = utils.key_hash(ss_key)
    ss_nonce = utils.nonce_hash(ss_nonce)

    key_exchange_time = time.time() - t

    # Receive and decrypt video frames
    while True:
        frame_time_start = time.time()
        # Measure transmission time
        t = time.time()
        ciphertext = client_socket.recv(131072)  # Adjust buffer size as needed

        if not ciphertext:
            break
        transmission_time = time.time() - t

        # Decrypt the frame
        t = time.time()
        decrypted_frame_bytes = utils.decrypt_message_chacha20(ss_key, ss_nonce, ciphertext)
        decryption_time = time.time() - t

        # Decode the JPEG frame
        t = time.time()
        frame = cv2.imdecode(np.frombuffer(decrypted_frame_bytes, np.uint8), cv2.IMREAD_COLOR)
        decode_time = time.time() - t

        finish_frame_time = time.time() - frame_time_start

        # Overlay statistics on the frame
        stats_text = (
            f"Client RSA Key Generation Time: {client_rsa_gen_time:.6f}s\n"
            f"Host RSA Key Generation Time: {host_rsa_gen_time:.6f}s\n"
            f"RSA Key Exchange Time: {key_exchange_time:.6f}s\n"
            f"Transmission Time: {transmission_time:.6f}s\n"
            f"Decryption Time: {decryption_time:.6f}s\n"
            f"Decoding Time: {decode_time:.6f}s\n"
            f"Frame Time: {finish_frame_time:.6f}s"
        )
        x, y = 10, 30
        for i, line in enumerate(stats_text.split('\n')):
            cv2.putText(frame, line, (x, y + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
        # Display the frame
        cv2.imshow('Decrypted Frame - ChaCha20', frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    client_socket.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_client(YOUR_PI_ADDRESS, 12345)