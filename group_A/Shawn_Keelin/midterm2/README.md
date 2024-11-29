# Encrypted Video Streaming from Raspberry Pi to PC

## Overview

This project enables encrypted video streaming from a Raspberry Pi to a PC using a USB webcam. The encryption is implemented using a 256-bit AES key derived from a secure Elliptic Curve Diffie-Hellman (ECDH) key exchange, which is secured using 2048-bit RSA encryption. The RSA keys are generated using a Montgomery prime number generator.

## Features

- **AES Encryption**: Utilizes a 256-bit AES key for video frame encryption.
- **RSA Encryption**: Employs a 2048-bit RSA key for securing the key exchange.
- **ECDH Key Exchange**: Implements a secure key exchange protocol using Elliptic Curve Diffie-Hellman.
- **Multiple AES Block Modes**: Supports testing of different AES modes (CBC, CFB, GCM).
- **Performance Evaluation**:
  - Measures execution time for the ECDH key exchange.
  - Measures execution time for packet transmission.
  - Provides numerical evaluations for the Elliptic Curve (EC) implementations.
  - Displays performance analysis overlayed on the video stream.
- **Error Handling**: Includes `try-except` blocks for robust error handling.
- **Camera Retry Mechanism**: Continuously attempts to open the camera every second if it fails.

## Prerequisites

- **Raspberry Pi** with a USB webcam.
- **PC** with Python 3.x installed.
- **Libraries**:
  - OpenCV (`cv2`)
  - PyCryptodome (`pycryptodome`)
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

## Code Overview

### `sender.py` (Raspberry Pi)

- **Key Exchange**:
  - Generates RSA key pair (2048 bits).
  - Exchanges RSA public keys with the PC.
  - Performs ECDH key exchange using the SECP256R1 curve.
  - Measures and prints the key exchange time.
  - Sends the ECDH key size to the PC.

- **Video Capture and Transmission**:
  - Continuously attempts to open the camera every second until successful.
  - Captures video frames using OpenCV.
  - Encrypts each frame using AES with the derived key and selected block mode.
  - Measures and records packet transmission times.
  - Sends encrypted frames to the PC.
  - Prints average packet transmission time every 30 frames.

### `receiver.py` (PC)

- **Key Exchange**:
  - Generates RSA key pair (2048 bits).
  - Exchanges RSA public keys with the Raspberry Pi.
  - Performs ECDH key exchange using the SECP256R1 curve.
  - Measures and prints the key exchange time.
  - Receives the ECDH key size from the Raspberry Pi.

- **Video Reception and Display**:
  - Receives encrypted frames from the Raspberry Pi.
  - Decrypts each frame using AES with the derived key and selected block mode.
  - Measures and records packet transmission times.
  - Decodes and displays the video frames using OpenCV.
  - Overlays performance metrics on the video frames.

## Usage

### On the PC (Receiver)

1. **Edit `receiver.py`**:
   - Ensure the `PORT` matches the one used in `sender.py`.
   - Optionally, change `AES_MODE` to match the sender's AES mode.
     ```python
     AES_MODE = AES.MODE_CBC  # Options: AES.MODE_CBC, AES.MODE_CFB, AES.MODE_GCM
     ```
2. **Run the receiver script**:
   ```bash
   python receiver.py
   ```

### On the Raspberry Pi (Sender)

1. **Edit `sender.py`**:
   - Replace `'PC_IP_ADDRESS'` with your PC's actual IP address.
     ```python
     HOST = 'PC_IP_ADDRESS'  # Replace with your PC's IP address
     ```
   - Optionally, change `AES_MODE` to test different AES block modes.
     ```python
     AES_MODE = AES.MODE_CBC  # Options: AES.MODE_CBC, AES.MODE_CFB, AES.MODE_GCM
     ```
2. **Run the sender script**:
   ```bash
   python sender.py
   ```

### Termination

- Press `q` on the PC window to quit the video stream.

## Troubleshooting

- **Connection Issues**:
  - Ensure that the Raspberry Pi can reach the PC over the network.
  - Check firewall settings that may block incoming connections on the PC.

- **Encryption/Decryption Errors**:
  - Verify that both the sender and receiver are using the same AES mode.
  - Ensure that the key exchange was successful before attempting to send video frames.

- **Camera Access Issues**:
  - Confirm that the camera is properly connected to the Raspberry Pi.
  - Check for necessary permissions to access the camera device.

- **Performance Metrics Not Displaying**:
  - Ensure that the OpenCV `cv2.putText()` function is correctly implemented.
  - Check for any errors in the console that might indicate issues with the overlay.

## Performance Evaluation

The code measures and displays execution times for:

- **ECDH Key Exchange**: Time taken to complete the Elliptic Curve Diffie-Hellman key exchange.
- **Packet Transmission**: Time taken to send and receive video frames.
- **Elliptic Curve Key Size**: Size of the ECDH public key used, in bits.

### Displaying Performance Metrics

- **On-Screen Display**: Performance metrics are overlayed on the video frames using OpenCV's `cv2.putText()` function.
  - Metrics displayed include:
    - **Key Exchange Time**
    - **Average Packet Transmission Time** (over the last 30 frames)
    - **Elliptic Curve Key Size**
- **Console Output**: Additional performance metrics and messages are printed to the console.

### Testing Multiple AES Block Modes

To test different AES modes, modify the `AES_MODE` variable in both `sender.py` and `receiver.py`:

```python
# Options: AES.MODE_CBC, AES.MODE_CFB, AES.MODE_GCM
AES_MODE = AES.MODE_CBC
```

Ensure that both the sender and receiver are using the same AES mode.

### Numerical Evaluations for Elliptic Curve Implementations

The implementation uses Elliptic Curve Diffie-Hellman (ECDH) for the key exchange:

- **Elliptic Curve Used**: SECP256R1
- **Key Size**: Displayed in bits (e.g., 256 bits)
- **Performance Metrics**: Key exchange time and key size are displayed on the video stream.

## Error Handling

- **Exception Handling**: The code includes `try-except` blocks to handle exceptions during camera access, key exchange, and data transmission.
- **Camera Retry Mechanism**: If the camera fails to open, the Raspberry Pi will retry every second until successful.

## Notes

- **Network Requirements**: Ensure that both devices are on the same network.
- **IP Address Configuration**: Replace placeholders like `'PC_IP_ADDRESS'` with the actual IP address of your PC.
- **Consistency in AES Modes**: Both sender and receiver must use the same AES mode for encryption and decryption to work correctly.

## Optional Future Enhancements

- **Logging Performance Data**: Modify the code to write performance metrics to a log file for later analysis.
- **Performance Graphs**: Use a library like Matplotlib to generate graphs from the logged performance data.
- **Dynamic AES Mode Selection**: Implement command-line arguments or a configuration file to change the AES mode without modifying the code.
- **GUI Integration**: Create a graphical interface to display performance metrics dynamically (e.g., using Tkinter or PyQt).

## Acknowledgments

- **OpenCV**: For video capture and display.
- **PyCryptodome**: For AES encryption and decryption.
- **Cryptography Library**: For RSA and ECDH key exchange implementations.
- **NumPy**: For efficient array handling and frame decoding.

## License

This project is licensed under the MIT License.
