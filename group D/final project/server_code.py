from flask import Flask, request, jsonify, send_from_directory
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
import os
import time 
from threading import Timer
import tracemalloc

app = Flask(__name__)

# Generate long-term key
long_term_private_key = ec.generate_private_key(ec.SECP256R1())
long_term_public_key = long_term_private_key.public_key()

# Generate signed pre-key
signed_pre_key_private = ec.generate_private_key(ec.SECP256R1())
signed_pre_key_public = signed_pre_key_private.public_key()

# Serialize the signed pre-key public key to bytes
signed_pre_key_bytes = signed_pre_key_public.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Hash the signed pre-key bytes before signing
digest = hashes.Hash(hashes.SHA256())
digest.update(signed_pre_key_bytes)
hashed_signed_pre_key = digest.finalize()

# Sign the hashed data
signature = long_term_private_key.sign(
    hashed_signed_pre_key,
    ec.ECDSA(hashes.SHA256()))


# Generate a batch of one-time keys
one_time_keys = [ec.generate_private_key(ec.SECP256R1()) for _ in range(10)]

pre_key_bundle = {
    "long_term_public_key": long_term_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode(),
    "signed_pre_key": signed_pre_key_public.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode(),
    "signature": signature.hex(),
    "one_time_keys": [
        key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode() for key in one_time_keys
    ]
}

@app.route("/", methods = ["GET"])
def welcome():
    return jsonify("Welcome")

@app.route("/prekey_bundle", methods=["GET"])
def get_prekey_bundle():
    return jsonify(pre_key_bundle)

#Global session_key array
session_key_registry = []

@app.route("/key_exchange", methods=["POST"])
def key_exchange():
    try:
        client_long_term_key = serialization.load_pem_public_key(
            request.json["client_long_term_key"].encode()
        )
        # Deserialize client ephemeral public key received from the client
        client_ephemeral_key = serialization.load_pem_public_key(
        request.json["client_ephemeral_key"].encode())

        # Serialize the key again for comparison
        client_ephemeral_key_pem = client_ephemeral_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo).decode()

        print("Server - Client Ephemeral Public Key Received (PEM):", client_ephemeral_key_pem)


        # Select a one-time key (use and remove it)
        one_time_key = one_time_keys.pop(0)
        one_time_public = one_time_key.public_key()

        # Debugging
        one_time_key_pem = one_time_public.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        print("Server - One-Time Key Public (PEM):", one_time_key_pem)

        # Compute shared secrets
        
        shared_secret_1 = signed_pre_key_private.exchange(ec.ECDH(), client_ephemeral_key)
        print("Server - Shared Secret 1:", shared_secret_1.hex())

        shared_secret_2 = long_term_private_key.exchange(ec.ECDH(), client_ephemeral_key)
        print("Server - Shared Secret 2:", shared_secret_2.hex())

        shared_secret_3 = one_time_key.exchange(ec.ECDH(), client_ephemeral_key)
        print("Server - Shared Secret 3:", shared_secret_3.hex())


        # Derive the session key (concatenate secrets and hash)
        from hashlib import sha256
        session_key = sha256(shared_secret_1 + shared_secret_2 + shared_secret_3).digest()
        session_key_registry.append(base64.b64encode(session_key).decode())
        print("Server - Raw Session Key (Bytes):", session_key)
        print("Server - Session Key (Base64):", base64.b64encode(session_key).decode())
        

        return jsonify({
            "session_key": base64.b64encode(session_key).decode(),
            "one_time_key": one_time_public.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/session_key_registry", methods=["GET"])
def get_session_key_registry():
    return jsonify(session_key_registry)

@app.route("/encrypt", methods=["POST"])
def encrypt():
    try:
    
        # Start performance metrics
        tracemalloc.start()
        start_time = time.time()

        # Debugging: Log raw request data
        print("Raw Request Data:", request.data)  # Logs raw payload
        print("Request Content-Type:", request.content_type)  # Logs content type

        # Parse JSON data from the request
        request_data = request.json
        print("Parsed Request JSON:", request_data)  # Logs parsed JSON

        # Retrieve plaintext and session key
        plaintext = request_data.get("plaintext")
        session_key = request_data.get("session_key")

        # Debugging prints to verify data
        print("Received Plaintext on Server:", plaintext)
        print("Received Session Key on Server (Base64):", session_key)

        if not plaintext:
            return jsonify({"error": "No plaintext provided"}), 400
        if not session_key:
            return jsonify({"error": "No session key provided"}), 400

        # Decode the session key (if it was sent as a base64-encoded string)
        session_key = base64.b64decode(session_key)

        # Ensure the session key is exactly 32 bytes long for AES-256
        if len(session_key) != 32:
            return jsonify({"error": f"Incorrect AES key length ({len(session_key)} bytes)."}), 400

        # Generate a random nonce
        nonce = get_random_bytes(12)
        print("Generated Nonce:", base64.b64encode(nonce).decode())
        
        # Encrypt using AES-GCM
        cipher = AES.new(session_key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())

        # Stop performance metrics
        end_time = time.time()
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Log performance metrics
        print(f"Encryption Time (ms): {round((end_time - start_time) * 1000, 2)}")
        print(f"Current Memory Usage (KB): {round(current_memory / 1024, 2)}")
        print(f"Peak Memory Usage (KB): {round(peak_memory / 1024, 2)}")

        # Return the ciphertext, nonce, tag, and performance metrics (all base64-encoded)
        return jsonify({
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "tag": base64.b64encode(tag).decode(),
            "encryption_time_ms": round((end_time - start_time) * 1000, 2),
            "current_memory_kb": round(current_memory / 1024, 2),
            "peak_memory_kb": round(peak_memory / 1024, 2)
        }), 200
    except Exception as e:
        print("Error during encryption:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/decrypt", methods=["POST"])
def decrypt():
    try:
        import time
        import tracemalloc

        # Start performance metrics
        tracemalloc.start()
        start_time = time.time()

        # Parse JSON data from the request
        request_data = request.json
        ciphertext = base64.b64decode(request_data.get("ciphertext"))
        nonce = base64.b64decode(request_data.get("nonce"))
        tag = base64.b64decode(request_data.get("tag"))
        session_key = request_data.get("session_key")

        # Debugging prints to verify received data
        print("Received Ciphertext (Base64):", request_data.get("ciphertext"))
        print("Received Nonce (Base64):", request_data.get("nonce"))
        print("Received Tag (Base64):", request_data.get("tag"))
        print("Received Session Key (Base64):", session_key)

        if not ciphertext or not nonce or not tag or not session_key:
            return jsonify({"error": "Missing required fields"}), 400

        # Ensure the session key is exactly 32 bytes long for AES-256
        if len(base64.b64decode(session_key)) != 32:
            print (base64.b64decode(session_key))
            return jsonify({"error": f"Incorrect AES key length ({len(session_key)} bytes)."}), 400
        

        # Check if the session key exists in the registry
        if session_key not in session_key_registry:
            print("Session Key is invalid")
            return jsonify({"error": "Invalid session key provided."}), 400
        else:
            print("Session Key is valid, proceeding with decryption")

        # Decode the session key
        session_key_bytes = base64.b64decode(session_key)

        # Decrypt using AES-GCM
        cipher = AES.new(session_key_bytes, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)

        # Stop performance metrics
        end_time = time.time()
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Log performance metrics
        print(f"Decryption Time (ms): {round((end_time - start_time) * 1000, 2)}")
        print(f"Current Memory Usage (KB): {round(current_memory / 1024, 2)}")
        print(f"Peak Memory Usage (KB): {round(peak_memory / 1024, 2)}")

        # Return the plaintext along with performance metrics
        return jsonify({
            "plaintext": plaintext.decode(),
            "decryption_time_ms": round((end_time - start_time) * 1000, 2),
            "current_memory_kb": round(current_memory / 1024, 2),
            "peak_memory_kb": round(peak_memory / 1024, 2)
        }), 200

    except Exception as e:
        # Debugging print for errors
        print("Error during decryption:", str(e))
        return jsonify({"error": str(e)}), 500
    
# Configure the upload folder and maximum file size
UPLOAD_FOLDER = "uploads/"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# File retention duration in seconds
FILE_RETENTION_DURATION = 600  # 10 minutes

def delete_file(filepath):
    """Deletes a file after the specified retention duration."""
    try:
        os.remove(filepath)
        print(f"Deleted file: {filepath}")
    except Exception as e:
        print(f"Error deleting file {filepath}: {str(e)}")


@app.route("/encrypt_file", methods=["POST"])
def encrypt_file():
    try:
        # Start performance metrics
        tracemalloc.start()
        start_time = time.time()

        # Check if session key is provided
        session_key_base64 = request.form.get("session_key")
        if not session_key_base64:
            return jsonify({"error": "Session key not provided"}), 400

        # Decode session key
        session_key = base64.b64decode(session_key_base64)
        if len(session_key) != 32:  # AES-256 requires a 32-byte key
            return jsonify({"error": f"Invalid session key length: {len(session_key)} bytes"}), 400

        # Check if a file is provided
        uploaded_file = request.files.get("file")
        if not uploaded_file:
            return jsonify({"error": "No file uploaded"}), 400

        # Read the file content into memory
        plaintext = uploaded_file.read()

        # Generate a random nonce for AES-GCM
        nonce = get_random_bytes(12)

        # Encrypt the file content
        cipher = AES.new(session_key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)

        # Stop performance metrics
        end_time = time.time()
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Log performance metrics
        print(f"Encryption Time (ms): {round((end_time - start_time) * 1000, 2)}")
        print(f"Current Memory Usage (KB): {round(current_memory / 1024, 2)}")
        print(f"Peak Memory Usage (KB): {round(peak_memory / 1024, 2)}")

        # Save the encrypted file
        encrypted_file_name = f"{uploaded_file.filename}.enc"
        encrypted_filepath = os.path.join(app.config['UPLOAD_FOLDER'], encrypted_file_name)
        with open(encrypted_filepath, "wb") as enc_file:
            enc_file.write(ciphertext)

        # Schedule the encrypted file for deletion after the retention duration
        Timer(FILE_RETENTION_DURATION, delete_file, args=[encrypted_filepath]).start()

        print(f"Encrypted file saved: {encrypted_filepath}")

        # Generate the download URL
        server_host = request.host_url.rstrip('/')  # Dynamically determine the server host
        encrypted_file_url = f"{server_host}/download/{encrypted_file_name}"

        # Return the encryption details to the client
        return jsonify({
            "message": "File encrypted successfully",
            "encrypted_file_url": encrypted_file_url,
            "nonce": base64.b64encode(nonce).decode(),
            "tag": base64.b64encode(tag).decode(),
            "encryption_time_ms": round((end_time - start_time) * 1000, 2),
            "current_memory_kb": round(current_memory / 1024, 2),
            "peak_memory_kb": round(peak_memory / 1024, 2)
        }), 200

    except Exception as e:
        print(f"Error during file encryption: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    try:
        # Construct the full file path in the uploads directory
        file_path = os.path.join("uploads", filename)

        # Check if the file exists
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404

        # Serve the file as a downloadable attachment
        return send_from_directory("uploads", filename, as_attachment=True)
    except Exception as e:
        print(f"Error during file download: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/decrypt_file", methods=["POST"])
def decrypt_file():
    try:
        # Start performance metrics
        tracemalloc.start()
        start_time = time.time()

        # Retrieve and validate inputs
        session_key_base64 = request.form.get("session_key")
        nonce_base64 = request.form.get("nonce")
        tag_base64 = request.form.get("tag")
        uploaded_file = request.files.get("file")

        # Debug: Print received inputs
        print("Debug: Received session_key (Base64):", session_key_base64)
        print("Debug: Received nonce (Base64):", nonce_base64)
        print("Debug: Received tag (Base64):", tag_base64)
        print("Debug: Received file:", uploaded_file.filename if uploaded_file else "No file uploaded")

        # Validate inputs
        if not session_key_base64 or not nonce_base64 or not tag_base64 or not uploaded_file:
            return jsonify({"error": "Missing required decryption parameters."}), 400

        # Decode session key, nonce, and tag
        try:
            session_key = base64.b64decode(session_key_base64)
            nonce = base64.b64decode(nonce_base64)
            tag = base64.b64decode(tag_base64)
        except Exception as decode_error:
            print(f"Debug: Base64 decoding error: {str(decode_error)}")
            return jsonify({"error": "Failed to decode Base64 values."}), 400

        # Validate session key length
        if len(session_key) != 32:  # AES-256 requires a 32-byte key
            print(f"Debug: Invalid session key length: {len(session_key)} bytes")
            return jsonify({"error": f"Invalid session key length: {len(session_key)} bytes"}), 400

        # Read the uploaded encrypted file
        try:
            encrypted_data = uploaded_file.read()
        except Exception as file_read_error:
            print(f"Debug: Error reading uploaded file: {str(file_read_error)}")
            return jsonify({"error": "Failed to read the uploaded file."}), 400

        # Decrypt the file content
        try:
            cipher = AES.new(session_key, AES.MODE_GCM, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(encrypted_data, tag)
        except ValueError as decryption_error:
            print(f"Debug: Decryption error: {str(decryption_error)}")
            return jsonify({"error": f"Decryption failed: {str(decryption_error)}"}), 400
        
        # Stop performance metrics
        end_time = time.time()
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Log performance metrics
        print(f"Encryption Time (ms): {round((end_time - start_time) * 1000, 2)}")
        print(f"Current Memory Usage (KB): {round(current_memory / 1024, 2)}")
        print(f"Peak Memory Usage (KB): {round(peak_memory / 1024, 2)}")

        # Save the decrypted file
        original_name = uploaded_file.filename
        if original_name.endswith('.enc'):
            decrypted_filename = f"decrypted_{original_name[:-4]}"
        else:
            decrypted_filename = f"decrypted_{original_name}"
        
        decrypted_filepath = os.path.join(app.config['UPLOAD_FOLDER'], decrypted_filename)
        try:
            with open(decrypted_filepath, "wb") as dec_file:
                dec_file.write(plaintext)
            print(f"Debug: Decrypted file saved at: {decrypted_filepath}")
        except Exception as file_save_error:
            print(f"Debug: Error saving decrypted file: {str(file_save_error)}")
            return jsonify({"error": "Failed to save decrypted file."}), 500

        # Generate a download URL for the decrypted file
        server_host = request.host_url.rstrip('/')
        download_url = f"{server_host}/download/{decrypted_filename}"

        # Schedule the decrypted file for deletion after retention period
        Timer(FILE_RETENTION_DURATION, delete_file, args=[decrypted_filepath]).start()

        # Return success response with download link
        return jsonify({
            "message": "File decrypted successfully",
            "decrypted_file": decrypted_filename,
            "download_url": download_url,
            "encryption_time_ms": round((end_time - start_time) * 1000, 2),
            "current_memory_kb": round(current_memory / 1024, 2),
            "peak_memory_kb": round(peak_memory / 1024, 2)
        }), 200

    except Exception as e:
        # General exception handler
        print(f"Error during file decryption: {str(e)}")
        return jsonify({"error": "An unexpected error occurred during decryption."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
