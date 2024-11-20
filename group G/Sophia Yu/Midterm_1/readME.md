# Video Encryption and Decryption with ChaCha20 Cipher

This project demonstrates how to record a video file (in MP4 format), encrypt it using the ChaCha20 encryption algorithm, and securely transfer it from a Raspberry Pi to another Linux computer for decryption.

video: https://youtu.be/px0jtZY_4dc?si=SYEVtgRFPKydKG79

---

## **Overview**

### Features:
1. **Video File Encryption:**
   - Encrypt an MP4 video file using the ChaCha20 cipher from the `cryptography.hazmat.primitives.ciphers` library.
   - Randomly generated `key` and `nonce` are used for encryption.

2. **Secure File Transfer:**
   - The encrypted video file is transferred from a Raspberry Pi to another Linux system using `scp`.

3. **Decryption on Target System:**
   - The video file is decrypted back to its original format on the Linux machine.

---

## **How It Works**

### **1. Encryption (Raspberry Pi)**
- The MP4 video file is read as plaintext.
- The ChaCha20 cipher is initialized with a randomly generated 256-bit (32-byte) `key` and a 96-bit (12-byte) `nonce`.
- The video file content is encrypted and saved as a new file.

### **2. Transfer the Encrypted File**
- The encrypted file, along with the `key` and `nonce`, is securely transferred to the target Linux computer using `scp`.

### **3. Decryption (Linux Machine)**
- The encrypted file is decrypted using the same `key` and `nonce`, restoring the original MP4 video file.

---

## **Setup Instructions**

### **Requirements**
1. **Raspberry Pi:**
   - Python 3.x
   - `cryptography` library: Install using `pip install cryptography`
   - Video file to encrypt (MP4 format).

2. **Linux Machine:**
   - Python 3.x
   - `cryptography` library: Install using `pip install cryptography`

3. **Network Connection:**
   - SSH access from Raspberry Pi to the Linux computer.

---
