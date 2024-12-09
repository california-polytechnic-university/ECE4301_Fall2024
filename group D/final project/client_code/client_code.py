from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
from hashlib import sha256
import requests

app = Flask(__name__)

# Update the server's IP address
SERVER_URL = "http://127.0.0.1:5000"

# Flask session configuration
app.config["SECRET_KEY"] = "your_secret_key"  # Replace with a strong secret key
app.config["SESSION_TYPE"] = "filesystem"    # Store sessions on the server's filesystem
Session(app)

# Store client long-term private key
CLIENT_LONG_TERM_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())

# Helper function to serialize public keys
def serialize_key(public_key):
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

# Route: Fetch and display the server pre-key bundle
@app.route("/prekey_bundle", methods=["GET"])
def fetch_prekey_bundle():
    response = requests.get(f"{SERVER_URL}/prekey_bundle")
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to fetch pre-key bundle"}), response.status_code

# Route: Perform X3DH and derive session key
import base64
from hashlib import sha256

@app.route("/key_exchange", methods=["POST"])
def key_exchange():
    # Fetch the pre-key bundle from the server
    response = requests.get(f"{SERVER_URL}/prekey_bundle")
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch pre-key bundle"}), response.status_code

    pre_key_bundle = response.json()

    # Load server keys from pre-key bundle
    server_long_term_key = serialization.load_pem_public_key(pre_key_bundle["long_term_public_key"].encode())
    server_signed_pre_key = serialization.load_pem_public_key(pre_key_bundle["signed_pre_key"].encode())

    # Debugging: Log the one-time key received from the server
    print("Client - One-Time Key Public (PEM):", pre_key_bundle["one_time_keys"][0])

    # Generate client ephemeral key pair
    client_ephemeral_private = ec.generate_private_key(ec.SECP256R1())
    client_ephemeral_public = client_ephemeral_private.public_key()

    # Serialize client ephemeral public key
    client_ephemeral_public_pem = client_ephemeral_public.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo).decode()

    print("Client - Ephemeral Public Key Sent to Server (PEM):", client_ephemeral_public_pem)

    # Send client public keys to the server for key exchange
    payload = {
        "client_long_term_key": serialize_key(CLIENT_LONG_TERM_PRIVATE_KEY.public_key()),
        "client_ephemeral_key": serialize_key(client_ephemeral_public),
    }
    response = requests.post(f"{SERVER_URL}/key_exchange", json=payload)

    if response.status_code != 200:
        return jsonify({"error": "Key exchange failed"}), response.status_code

    # Extract the one-time key and session key from the server's response
    server_response = response.json()
    session_key_base64 = server_response["session_key"]
    one_time_key = serialization.load_pem_public_key(server_response["one_time_key"].encode())

    print("Client - One-Time Key Received from Server (PEM):", server_response["one_time_key"])

    # Compute shared secrets using Diffie-Hellman
    # Shared Secret 1
    shared_secret_1 = client_ephemeral_private.exchange(ec.ECDH(), server_signed_pre_key)
    print("Client - Shared Secret 1:", shared_secret_1.hex())

    # Shared Secret 2
    shared_secret_2 = client_ephemeral_private.exchange(ec.ECDH(), server_long_term_key)
    print("Client - Shared Secret 2:", shared_secret_2.hex())

    # Shared Secret 3
    shared_secret_3 = client_ephemeral_private.exchange(ec.ECDH(), one_time_key)
    print("Client - Shared Secret 3:", shared_secret_3.hex())

    # Verify that the computed session key matches the server-provided session key
    combined_shared_secrets = shared_secret_1 + shared_secret_2 + shared_secret_3
    computed_session_key = sha256(combined_shared_secrets).digest()  # SHA-256 produces a 32-byte key
    computed_session_key_base64 = base64.b64encode(computed_session_key).decode()

    print("Client - Computed Session Key (Base64):", computed_session_key_base64)
    print("Client - Server-Provided Session Key (Base64):", session_key_base64)

    if computed_session_key_base64 != session_key_base64:
        print("Warning: Computed session key does not match the server-provided session key!")

    # Store the session key in the Flask session
    session["session_key"] = session_key_base64
    print("Session Key Stored in Flask Session (Base64):", session["session_key"])

    return jsonify({"message": "Key exchange successful", "session_key": session_key_base64})
 
    

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/plaintext-encrypt-page")
def plaintext_encrypt_page():
    return render_template("plaintext_encrypt.html")  


# Route: Encrypt data using session key
@app.route("/encrypt", methods=["POST"])
def encrypt():
    # Retrieve the session key from the session
    session_key = session.get("session_key")
    print("Retrieved Session Key in Encrypt Route:", session_key)  # Debug print
    if not session_key:
        return jsonify({"error": "Session key not established. Perform key exchange first."}), 400

    # Parse JSON payload
    request_data = request.json
    print("Received Request JSON:", request_data)  # Debug print

    # Retrieve plaintext from JSON
    plaintext = request_data.get("plaintext")
    if not plaintext:
        return jsonify({"error": "No plaintext provided"}), 400

    # Debugging payload to be sent to the server
    payload = {"plaintext": plaintext, "session_key": session_key}
    print("Payload Sent to Server:", payload)  # Debug print

    # Forward the payload to the server for encryption
    response = requests.post(f"{SERVER_URL}/encrypt", json=payload)

    # Extract the server response
    server_response = response.json()

    # If the response contains an error, return it
    if "error" in server_response:
        return jsonify(server_response)

    # Extract metrics
    encryption_time = server_response.get("encryption_time_ms", "N/A")
    current_memory = server_response.get("current_memory_kb", "N/A")
    peak_memory = server_response.get("peak_memory_kb", "N/A")

    # Add metrics to the response
    return jsonify({
        "ciphertext": server_response.get("ciphertext"),
        "nonce": server_response.get("nonce"),
        "tag": server_response.get("tag"),
        "encryption_time_ms": encryption_time,
        "current_memory_kb": current_memory,
        "peak_memory_kb": peak_memory
    })


@app.route("/plaintext-decrypt-page")
def plaintext_decrypt_page():
    return render_template("plaintext_decrypt.html")  

# Route: Decrypt data using session key
@app.route("/decrypt", methods=["POST"])
def decrypt():
    # Parse the JSON payload
    request_data = request.json
    print("Received Request JSON:", request_data)  # Debug print

    # Retrieve the necessary fields from the JSON payload
    ciphertext = request_data.get("ciphertext")
    nonce = request_data.get("nonce")
    tag = request_data.get("tag")
    session_key = request_data.get("session_key")

    # Ensure all required fields are provided
    if not ciphertext or not nonce or not tag or not session_key:
        return jsonify({"error": "Missing ciphertext, nonce, tag, or session key"}), 400

    # Debugging the payload to be sent to the server
    payload = {
        "ciphertext": ciphertext,
        "nonce": nonce,
        "tag": tag,
        "session_key": session_key,
    }
    print("Payload Sent to Server for Decryption:", payload)

    # Forward the payload to the backend decryption server
    response = requests.post(f"{SERVER_URL}/decrypt", json=payload)

    # Extract the server response
    server_response = response.json()

    # If the response contains an error, return it
    if "error" in server_response:
        return jsonify(server_response)

    # Extract metrics
    decryption_time = server_response.get("decryption_time_ms", "N/A")
    current_memory = server_response.get("current_memory_kb", "N/A")
    peak_memory = server_response.get("peak_memory_kb", "N/A")

    # Add metrics to the response
    return jsonify({
        "plaintext": server_response.get("plaintext"),
        "decryption_time_ms": decryption_time,
        "current_memory_kb": current_memory,
        "peak_memory_kb": peak_memory
    })

@app.route("/file-encrypt-page")
def file_encrypt_page():
    return render_template("file_encrypt.html")

@app.route("/upload", methods=["POST"])
def client_upload():
    # Check if file is in the request
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    # Get the file from the request
    file = request.files['file']

    # Check if the file has a valid name
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Forward the file to the server
    files = {'file': (file.filename, file.stream, file.mimetype)}
    response = requests.post(f"{SERVER_URL}/upload", files=files)

    # Return the server's response to the client
    return jsonify(response.json()), response.status_code  

@app.route("/encrypt_file", methods=["POST"])
def encrypt_file():
    try:
        # Retrieve the session key from the client's Flask session
        session_key_base64 = session.get("session_key")
        print("Retrieved Session Key from Client Session (Base64):", session_key_base64)

        if not session_key_base64:
            return jsonify({"error": "Session key not established. Perform key exchange first."}), 400

        # Check if a file was uploaded in the request
        uploaded_file = request.files.get("file")
        if not uploaded_file:
            return jsonify({"error": "No file uploaded"}), 400

        # Send the file and session key to the server for encryption
        files = {
            "file": (uploaded_file.filename, uploaded_file.stream, uploaded_file.mimetype)
        }
        data = {
            "session_key": session_key_base64  # Include the session key in the payload
        }

        # Make a POST request to the server-side encryption route
        response = requests.post(f"{SERVER_URL}/encrypt_file", files=files, data=data)
        server_response = response.json()

        # If the server returned an error, pass it back to the client
        if "error" in server_response:
            return jsonify(server_response), response.status_code
        
        if not server_response.get("encrypted_file_url"):
            return jsonify({"error": "Failed to retrieve download URL from server"}), 400


        # Return the server's response including encryption details
        return jsonify({
            "message": "File encrypted successfully",
            "encrypted_file_name": server_response.get("encrypted_file_name"),
            "encrypted_file_url": server_response.get("encrypted_file_url"),
            "nonce": server_response.get("nonce"),
            "tag": server_response.get("tag"),
            "download_link": server_response.get("encrypted_file_url"),
            "encryption_time_ms": server_response.get("encryption_time_ms", "N/A"),
            "current_memory_kb": server_response.get("current_memory_kb", "N/A"),
            "peak_memory_kb": server_response.get("peak_memory_kb", "N/A")  
        }), 200

    except Exception as e:
        print("Error during file encryption request:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/file-decrypt-page")
def file_decrypt_page():
    return render_template("file_decrypt.html")

@app.route("/decrypt_file", methods=["POST"])
def decrypt_file():
    try:
        # Retrieve the session key from the form
        session_key = request.form.get("session_key")
        nonce = request.form.get("nonce")
        tag = request.form.get("tag")
        encrypted_file = request.files.get("file")

        print("session key retrieved:", session_key)
        print("nonce retrieved:", nonce)
        print("tag retrieved:", tag)
        print("encrypted file retrieved", encrypted_file)

        if not session_key or not nonce or not tag or not encrypted_file:
            return jsonify({"error": "Missing required decryption parameters."}), 400

        # Prepare the file and data payload for the server
        files = {
            "file": (encrypted_file.filename, encrypted_file.stream, encrypted_file.mimetype)
        }
        data = {
            "session_key": session_key,
            "nonce": nonce,
            "tag": tag
        }

        # Send the decryption request to the server
        response = requests.post(f"{SERVER_URL}/decrypt_file", files=files, data=data)
        server_response = response.json()

        # If the server returned an error, propagate it back to the client
        if "error" in server_response:
            return jsonify(server_response), response.status_code

        # Return the server's response, including decrypted file details, back to the client
        return jsonify({
            "message": "File decrypted successfully",
            "decrypted_file": server_response.get("decrypted_file"),
            "download_url": server_response.get("download_url"),
            "encryption_time_ms": server_response.get("encryption_time_ms"),
            "current_memory_kb": server_response.get("current_memory_kb"),
            "peak_memory_kb": server_response.get("peak_memory_kb")
            
        }), 200

    except Exception as e:
        print("Error during file decryption request:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

