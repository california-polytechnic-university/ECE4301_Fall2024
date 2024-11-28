from Crypto.PublicKey import RSA

def generate_rsa_keys(bits=2048):
    key = RSA.generate(bits)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return private_key, public_key

def save_key(key, filename):
    with open(filename, 'wb') as f:
        f.write(key)

if __name__ == "__main__":
    private_key, public_key = generate_rsa_keys()
    save_key(private_key, "private_key.pem")
    save_key(public_key, "public_key.pem")
    print("RSA keys generated and saved.")