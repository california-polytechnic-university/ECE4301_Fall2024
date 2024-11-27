# Hybrid Cryptography for Secure File Transfer and Communication
This project demonstrates a hybrid cryptography system for securely exchanging random values, deriving a shared symmetric AES key, and using it to encrypt/decrypt a video file between a Host PC and a Raspberry Pi (PI). The system uses RSA and Diffie-Hallman for secure key exchange and AES for efficient symmetric encryption.

## Features

    1. RSA Key Exchange: Generates RSA key pairs for the Host PC and Raspberry Pi, allowing secure exchange of random values.
    2. Shared Key Derivation: Uses the exchanged random values to generate a shared AES key via HKDF (HMAC-based Key Derivation Function).
    3. AES Encryption/Decryption: Utilizes AES-CBC for secure encryption and decryption of large files (e.g., MP4 videos).
    4. File Transfer via SCP: Securely transfers files between Host PC and Raspberry Pi.

## Workflow
1. Host PC (First Code)

    Generate RSA Key Pair:
        Generates a private/public RSA key pair.
        Saves the keys as PEM files (LX_private_key.pem, LX_public_key.pem).

    Send Public Key to PI:
        Transfers LX_public_key.pem to the Raspberry Pi via SCP.

    Wait for PI's Public Key:
        Waits until the Raspberry Pi sends its public key (PI_public_key.pem).
        Loads the public key upon arrival.

    Generate Random Value:
        Creates a secure random value (LX_random_value).

    Encrypt and Send Random Value:
        Encrypts LX_random_value using PI's public key and sends it to the Raspberry Pi.

    Wait for PI's Encrypted Random Value:
        Waits for PI_encrypted_random_value.bin from the Raspberry Pi.
        Decrypts the received value using its private key to get PI_random_value.

    Derive Shared AES Key:
        Combines LX_random_value and PI_random_value to generate the AES key using HKDF.

    Decrypt Received Video:
        Waits for the encrypted video file (encrypted_video.enc).
        Decrypts it using the derived AES key and saves it as decrypted_video_haha.mp4.

2. Raspberry Pi (Second Code)

    Generate RSA Key Pair:
        Generates a private/public RSA key pair.
        Saves the keys as PEM files (PI_private_key.pem, PI_public_key.pem).

    Send Public Key to Host:
        Transfers PI_public_key.pem to the Host PC via SCP.

    Wait for Host's Public Key:
        Waits until the Host PC sends its public key (LX_public_key.pem).
        Loads the public key upon arrival.

    Generate Random Value:
        Creates a secure random value (PI_random_value).

    Encrypt and Send Random Value:
        Encrypts PI_random_value using the Host PC's public key and sends it to the Host PC.

    Wait for Host's Encrypted Random Value:
        Waits for LX_encrypted_random_value.bin from the Host PC.
        Decrypts the received value using its private key to get LX_random_value.

    Derive Shared AES Key:
        Combines PI_random_value and LX_random_value to generate the AES key using HKDF.

    Encrypt Video File:
        Encrypts a sample video (IMG_2853.mp4) using the derived AES key and saves it as encrypted_video.enc.

    Send Encrypted Video:
        Transfers encrypted_video.enc to the Host PC via SCP.
