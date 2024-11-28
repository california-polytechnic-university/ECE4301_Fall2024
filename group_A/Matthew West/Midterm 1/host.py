import utils, socket, cv2

def recv_all(sock, length):
    data = b''
    while len(data) < length:
        packet = sock.recv(length - len(data))
        if not packet:
            raise ConnectionError("Socket connection closed")
        data += packet
    return data


def start_server(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(1)
    print(f"Listening on port {port}...")

    conn, addr = server_socket.accept()
    print(f"Connection from {addr}")

    # Generate RSA key pair for the host
    host_n, host_e, host_d = utils.rsa_key_gen()
    host_private_rsa_key = (host_n, host_d)
    
    # Send the host's RSA public key
    conn.sendall(host_n.to_bytes((host_n.bit_length() + 7) // 8, 'big'))
    conn.sendall(host_e.to_bytes((host_e.bit_length() + 7) // 8, 'big'))

    # Receive Client's public key value
    client_n = int.from_bytes(conn.recv(2048), 'big')
    client_e = int.from_bytes(conn.recv(2048), 'big')
    client_public_rsa_key = (client_n, client_e)  # Client public key

    # Receive the lengths of the encrypted key and nonce from the client
    client_key_length = int.from_bytes(recv_all(conn, 4), 'big')
    client_nonce_length = int.from_bytes(recv_all(conn, 4), 'big')

    # Receive the encrypted key and nonce from the client
    encrypted_client_gen_key = recv_all(conn, client_key_length)
    encrypted_client_gen_nonce = recv_all(conn, client_nonce_length)

    # Decrypt the key and nonce using the host's private key
    client_gen_key = utils.decrypt_rsa(encrypted_client_gen_key, host_private_rsa_key)
    client_gen_nonce = utils.decrypt_rsa(encrypted_client_gen_nonce, host_private_rsa_key)

    # Generate cipher key and nonce
    host_gen_key = utils.gen_key()
    host_gen_nonce = utils.gen_nonce()

    # Encrypt the key and nonce using the client's public key
    encrypted_host_gen_key = utils.encrypt_rsa(host_gen_key, client_public_rsa_key)
    encrypted_host_gen_nonce = utils.encrypt_rsa(host_gen_nonce, client_public_rsa_key)

    # Send the lengths of the encrypted key and nonce
    conn.sendall(len(encrypted_host_gen_key).to_bytes(4, 'big'))
    conn.sendall(len(encrypted_host_gen_nonce).to_bytes(4, 'big'))

    # Send the encrypted key and nonce to the client
    conn.sendall(encrypted_host_gen_key)
    conn.sendall(encrypted_host_gen_nonce)

    # Derive the shared secret key and nonce
    ss_key = int.from_bytes(client_gen_key, byteorder='big') ^ int.from_bytes(host_gen_key, byteorder='big')
    ss_nonce = int.from_bytes(client_gen_nonce, byteorder='big') ^ int.from_bytes(host_gen_nonce, byteorder='big')

    # Hash the shared secret key and nonce
    ss_key = utils.key_hash(ss_key)
    ss_nonce = utils.nonce_hash(ss_nonce)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Failed to open camera")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame")
            break

        # Encode the frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            print("Failed to encode frame")
            break
        
        frame_bytes = buffer.tobytes()

        # Encrypt the frame using ChaCha20
        ciphertext = utils.encrypt_message_chacha20(ss_key, ss_nonce, frame_bytes)

        # Send the encrypted frame
        conn.sendall(ciphertext)
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    conn.close()
    server_socket.close()

if __name__ == "__main__":
    start_server(12345)