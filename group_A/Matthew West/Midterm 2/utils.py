import random, math, hashlib
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305, AESGCM
ENCRYPTION_WIDTH = 1024

def miller_rabin_primality_test(n, iterations):
    # Handle small cases for efficiency
    if n < 4:
        return n == 2 or n == 3
    # Find r and s such that n = 2^r * s + 1
    r, s = 0, n - 1
    while s % 2 == 0:
        r += 1
        s //= 2
    for _ in range(iterations):
        # Generate a random integer 'a' in the range [2, n-2]
        a = random.randint(2, n-2)
        # Compute a^s % n
        x = pow(a, s, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    
    # Probably prime if it passes all iterations
    return True

def rand_prime(bits):
    while True:
        # Generate a random odd number of 'bits' length
        n = random.getrandbits(bits) | (1 << bits) | 1
        # Check if n is prime using the Miller-Rabin primality test
        if miller_rabin_primality_test(n, 1000):
            return n

def mod_inv(a, m):
    m0, x0, x1 = m, 0, 1
    if m == 1:
        return 0
    while a > 1:
        q = a // m
        m, a = a % m, m
        x0, x1 = x1 - q * x0, x0
    if x1 < 0:
        x1 += m0
    return x1

def rsa_key_gen():
    p = rand_prime(ENCRYPTION_WIDTH)
    q = rand_prime(ENCRYPTION_WIDTH)
    while q == p:
        q = rand_prime(ENCRYPTION_WIDTH)
    n = p * q
    phi = (p - 1) * (q - 1)
    d = random.randint(2**15, 2**16 - 1)
    while math.gcd(d, phi) != 1:
        d += 1
    e = mod_inv(d, phi)
    return n, e, d

def encrypt_rsa(message, public_key):
    n, e = public_key
    message_int = int.from_bytes(message, byteorder='big')
    encrypted_message = pow(message_int, e, n)
    block_size = (n.bit_length() + 7) // 8
    return encrypted_message.to_bytes(block_size, byteorder='big')

def decrypt_rsa(ciphertext, private_key):
    n, d = private_key
    ciphertext_int = int.from_bytes(ciphertext, byteorder='big')
    decrypted_message = pow(ciphertext_int, d, n)
    block_size = (n.bit_length() + 7) // 8
    return decrypted_message.to_bytes(block_size, byteorder='big')

def gen_dh_public_params():
    p = rand_prime(ENCRYPTION_WIDTH*2)
    g = random.randint(2, p - 1)
    return p, g

def gen_dh_key_pair(dh_params):
    p, g = dh_params
    private_key = random.getrandbits(ENCRYPTION_WIDTH*2)
    public_key = pow(g, private_key, p)
    return private_key, public_key

def gen_dh_shared_secret(private_key, public_key, p):
    return pow(public_key, private_key, p)

def derive_shared_secret(private_key, public_key, p):
    return pow(public_key, private_key, p)

def encrypt_message_chacha20(key, nonce, plaintext):
    cipher = ChaCha20Poly1305(key)
    ct = cipher.encrypt(nonce, plaintext, None)
    return ct

def decrypt_message_chacha20(key, nonce, ciphertext):
    cipher = ChaCha20Poly1305(key)
    pt = cipher.decrypt(nonce, ciphertext, None)
    return pt

def encrypt_aes_gcm(key, nonce, plaintext):
    cipher = AESGCM(key)
    return cipher.encrypt(nonce, plaintext, None)

def decrypt_aes_gcm(key, nonce, ciphertext):
    cipher = AESGCM(key)
    return cipher.decrypt(nonce, ciphertext, None)

def gen_key():
    return random.getrandbits(256).to_bytes(32, 'big')

def gen_nonce():
    return random.getrandbits(96).to_bytes(12, 'big')

def nonce_hash(nonce):
    nonce = nonce.to_bytes((nonce.bit_length() + 7) // 8, byteorder='big')
    return hashlib.sha256(nonce).digest()[:12]

def key_hash(key):
    key = key.to_bytes((key.bit_length() + 7) // 8, byteorder='big')
    return hashlib.sha256(key).digest()[:32]
