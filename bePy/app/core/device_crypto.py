import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv
load_dotenv("./app/.env")



DEVICE_SECRET_KEY = os.getenv("DEVICE_SECRET_KEY")
if not DEVICE_SECRET_KEY:
    raise RuntimeError("DEVICE_SECRET_KEY not set")

hkdf = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=b"device-password-encryption",
    info=b"v1",
    backend=default_backend()
)

KEY = hkdf.derive(DEVICE_SECRET_KEY.encode())



def encrypt_device_password(plain: str) -> str:
    """
    Encrypt password for DB storage
    """
    aesgcm = AESGCM(KEY)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    encrypted = aesgcm.encrypt(nonce, plain.encode(), None)
    return base64.b64encode(nonce + encrypted).decode()


def decrypt_device_password(cipher_text: str) -> str:
    """
    Decrypt password for runtime use
    """
    raw = base64.b64decode(cipher_text)
    nonce = raw[:12]
    encrypted = raw[12:]
    aesgcm = AESGCM(KEY)
    return aesgcm.decrypt(nonce, encrypted, None).decode()
