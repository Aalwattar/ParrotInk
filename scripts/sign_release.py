import base64
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ed25519


def sign_file(input_file_path: str, output_sig_path: str):
    # 1. Read private key from environment variable (populated by GitHub Secrets)
    private_key_b64 = os.environ.get("PARROTINK_RELEASE_SIGNING_KEY")
    if not private_key_b64:
        print("Error: PARROTINK_RELEASE_SIGNING_KEY environment variable is not set.")
        sys.exit(1)

    try:
        # 2. Decode the private key
        private_bytes = base64.b64decode(private_key_b64.strip())
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)

        # 3. Read the checksum file content
        data = Path(input_file_path).read_bytes()

        # 4. Sign the checksum file
        signature = private_key.sign(data)

        # 5. Write the signature to a binary file (.sig)
        Path(output_sig_path).write_bytes(signature)
        print(f"Successfully signed {input_file_path} -> {output_sig_path}")

    except Exception as e:
        print(f"Error signing file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python sign_release.py <input_file> <output_sig>")
        sys.exit(1)
    sign_file(sys.argv[1], sys.argv[2])
