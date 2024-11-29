# Encrypted Video Streaming from Raspberry Pi to PC

## Overview

This project enables encrypted video streaming from a Raspberry Pi to a PC using a USB webcam. The encryption is implemented using a 256-bit AES key derived from a secure Diffie-Hellman key exchange, which is secured using 2048-bit RSA encryption. The RSA keys are generated using a Montgomery prime number generator.

## Features

- **AES Encryption**: Utilizes a 256-bit AES key for video frame encryption.
- **RSA Encryption**: Employs a 2048-bit RSA key for securing the key exchange.
- **Diffie-Hellman Key Exchange**: Implements a secure key exchange protocol.
- **Multiple Security Block Modes**: Supports testing of different AES modes (CBC, CFB, GCM).
- **Performance Evaluation**: Measures execution time for key exchange and packet transmission.
- **Error Handling**: Includes `try-except` blocks for robust error handling.
- **Camera Retry Mechanism**: Continuously attempts to open the camera every second if it fails.

## Prerequisites

- **Raspberry Pi** with a USB webcam.
- **PC** with Python 3.x installed.
- **Libraries**:
  - OpenCV (`cv2`)
  - PyCryptodome (`Crypto`)
  - Cryptography (`cryptography`)
  - NumPy (`numpy`)

## Installation

Install the required Python libraries on both the Raspberry Pi and the PC:

```bash
pip install opencv-python
pip install pycryptodome
pip install cryptography
pip install numpy
```

## Usage

### On the PC (Receiver)

1. **Edit `receiver.py`**:
   - Replace `HOST` and `PORT` if necessary.
2. **Run the receiver script**:
   ```bash
   python receiver.py
   ```

### On the Raspberry Pi (Sender)

1. **Edit `sender.py`**:
   - Replace `HOST` with the PC's IP address.
2. **Run the sender script**:
   ```bash
   python sender.py
   ```

### Termination

- Press `q` on the PC window to quit the video stream.

## Performance Evaluation

The code measures and displays execution times for:

- **Diffie-Hellman Protocol**: Time taken for the key exchange.
- **Packet Transmission**: Time taken to send and receive video frames.

### Displaying Performance Metrics

Performance metrics are printed to the console. You can modify the code to display these metrics in a dedicated box on the video stream window or generate performance graphs.

## Testing Multiple Security Block Modes

To test different AES modes, modify the AES cipher initialization in both `sender.py` and `receiver.py`:

```python
# For CBC mode
cipher = AES.new(aes_key, AES.MODE_CBC, iv)
# For CFB mode
cipher = AES.new(aes_key, AES.MODE_CFB, iv)
# For GCM mode
cipher = AES.new(aes_key, AES.MODE_GCM, iv)
```

## Numerical Evaluations for Elliptic Curve Implementations

The current implementation uses standard Diffie-Hellman. To evaluate Elliptic Curve Diffie-Hellman (ECDH):

1. Modify the key exchange section to use ECDH.
2. Measure and compare the execution times.

## Error Handling

- The code includes `try-except` blocks to handle exceptions during camera access, key exchange, and data transmission.
- If the camera fails to open, the Raspberry Pi will retry every second.

## Notes

- Ensure that both devices are on the same network.
- Replace placeholders like `PC_IP_ADDRESS` with actual IP addresses.

## Optional Enhancements

- **Performance Graphs**: Implement code to log performance data and generate graphs.
- **GUI Integration**: Create a graphical interface to display performance metrics dynamically.

## License

This project is licensed under the MIT License.
