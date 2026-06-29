import base64

from cryptography.hazmat.primitives.asymmetric import ed25519


def generate_keys():
    # 1. Generate a new private key
    private_key = ed25519.Ed25519PrivateKey.generate()

    # 2. Extract private bytes in raw form and encode in base64
    private_bytes = private_key.private_bytes_raw()
    private_b64 = base64.b64encode(private_bytes).decode("utf-8")

    # 3. Extract public bytes in raw form and encode in base64
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes_raw()
    public_b64 = base64.b64encode(public_bytes).decode("utf-8")

    print("=== PRIVATE KEY (Keep Secret! Add to GitHub Secrets) ===")
    print(private_b64)
    print("\n=== PUBLIC KEY (Will be embedded in engine/constants.py) ===")
    print(public_b64)


if __name__ == "__main__":
    generate_keys()
