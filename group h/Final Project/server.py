import time
import psutil
import os
from flask import Flask, render_template
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-flask-secret-key'
socketio = SocketIO(app)

participants = []
server_private_key = RSA.generate(2048)
server_public_key = server_private_key.publickey()
chatroom_session_key = get_random_bytes(16)  # Shared session key for the room
message_count = 0
start_time = time.time()


# Helper Functions for Metrics
def get_memory_usage():
    """Get memory usage of the server process."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # Convert to MB


def estimate_energy_consumption(start_time, end_time):
    """Estimate energy consumption based on time."""
    energy_constant = 0.05  # Arbitrary constant: 0.05 watts per second
    duration = end_time - start_time
    return duration * energy_constant  # Watts-seconds


def calculate_throughput():
    """Calculate the throughput in messages per second."""
    global message_count, start_time
    current_time = time.time()
    elapsed_time = current_time - start_time
    return message_count / elapsed_time if elapsed_time > 0 else 0


def get_disk_usage():
    """Get the disk usage of the system."""
    usage = psutil.disk_usage('/')
    return usage.used / 1024 / 1024  # Convert to MB


def get_network_bandwidth():
    """Get the network bandwidth usage."""
    net_io = psutil.net_io_counters()
    return net_io.bytes_sent / 1024, net_io.bytes_recv / 1024  # Convert to KB


def get_cpu_usage():
    """Get CPU usage of the server."""
    return psutil.cpu_percent(interval=1)  # Measure over 1 second


@app.route('/')
def home():
    return render_template('index.html')


@socketio.on('exchange_keys')
def exchange_keys(data):
    """Handle key exchange between server and client."""
    try:
        client_public_key_pem = data['client_public_key']
        client_public_key = RSA.import_key(client_public_key_pem)
        cipher_rsa = PKCS1_OAEP.new(client_public_key)

        # Encrypt the shared session key with the client's public key
        encrypted_session_key = cipher_rsa.encrypt(chatroom_session_key)
        print(f"Generated Shared Session Key (Hex): {chatroom_session_key.hex()}")  # Debug

        emit('server_keys', {
            'server_public_key': server_public_key.export_key().decode(),
            'encrypted_session_key': base64.b64encode(encrypted_session_key).decode()
        })
    except Exception as e:
        print(f"Key exchange error: {e}")


@socketio.on('message')
def handle_message(data):
    """Handle messages sent by clients."""
    global message_count
    message_count += 1
    sent_time = float(data.get('sent_time', 0))  # Client's sent timestamp
    server_time = time.time()

    try:
        username = data['username']
        encrypted_message = base64.b64decode(data['message'])  # Decode the base64-encoded message
        iv = encrypted_message[:16]  # Extract the IV (first 16 bytes)
        ciphertext = encrypted_message[16:]  # Extract the ciphertext
        timestamp = data['timestamp']

        # Decrypt the message
        decryption_start = time.time()
        cipher_aes = AES.new(chatroom_session_key, AES.MODE_CBC, iv)
        decrypted_message = unpad(cipher_aes.decrypt(ciphertext), AES.block_size).decode('utf-8')
        decryption_end = time.time()

        print(f"Decrypted Message from {username}: {decrypted_message} at {timestamp}")  # Debugging purpose
        
        avatar_url = f"https://robohash.org/{username}.png"
        
        # Metrics
        decryption_time = decryption_end - decryption_start
        latency = server_time - sent_time
        memory_usage = get_memory_usage()
        energy_consumption = estimate_energy_consumption(decryption_start, decryption_end)
        throughput = calculate_throughput()
        disk_usage = get_disk_usage()
        bytes_sent, bytes_received = get_network_bandwidth()
        cpu_usage = get_cpu_usage()
        

        # Logging
        print(f"Decrypted Message from {username}: {decrypted_message}")
        print(f"Decryption Time: {decryption_time:.6f} seconds")
        print(f"Latency: {latency:.6f} seconds")
        print(f"Throughput: {throughput:.2f} messages/second")
        print(f"Memory Usage: {memory_usage:.2f} MB")
        print(f"Disk Usage: {disk_usage:.2f} MB")
        print(f"Network Bandwidth - Sent: {bytes_sent:.2f} KB, Received: {bytes_received:.2f} KB")
        print(f"CPU Usage: {cpu_usage:.2f}%")
        print(f"Estimated Energy Consumption: {energy_consumption:.6f} watts-seconds")

        # Relay the encrypted message to all clients
        send({
            'type': 'user',
            'username': username,
            'avatar_url': avatar_url,
            'message': data['message'],  # Send the encrypted message for end-to-end encryption
            'timestamp': timestamp
        }, to="chatroom")
    except Exception as e:
        print(f"Message handling error: {e}")


@socketio.on('join')
def handle_join(data):
    """Handle a user joining the chatroom."""
    username = data['username']
    timestamp = data.get('timestamp') or time.strftime("%m/%d/%Y - %H:%M:%S")
    if username not in [p['name'] for p in participants]:
        participants.append({'name': username, 'timestamp': timestamp})
    join_room("chatroom")
    send({'type': 'system', 'message': f"{username} has joined the chatroom", 'timestamp': timestamp}, to="chatroom")
    emit('update_participants', participants, to="chatroom")


@socketio.on('leave')
def handle_leave(data):
    """Handle a user leaving the chatroom."""
    username = data['username']
    timestamp = data.get('timestamp') or time.strftime("%m/%d/%Y - %H:%M:%S")
    participants[:] = [p for p in participants if p['name'] != username]  # Remove user from participants list
    leave_room("chatroom")
    send({'type': 'system', 'message': f"{username} has left the chatroom", 'timestamp': timestamp}, to="chatroom")
    emit('update_participants', participants, to="chatroom")


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)

