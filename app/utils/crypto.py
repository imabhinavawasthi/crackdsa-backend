import os
import hashlib
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

# Retrieve secret or default fallback
_SECRET = getattr(settings, "MEDIA_ENCRYPTION_KEY", None) or os.getenv("MEDIA_ENCRYPTION_KEY", "crackdsa-secure-media-key-2026-production-vault")
_KEY = hashlib.sha256(_SECRET.encode("utf-8")).digest()
_CIPHER = AESGCM(_KEY)


def encrypt_media_url(url: Optional[str]) -> Optional[str]:
    """
    Encrypts a sensitive media link (Google Drive, live recording, zoom link)
    using AES-256-GCM so it is never exposed in plaintext across network responses.
    Format: enc:v1:<nonce_hex>:<ciphertext_hex>
    """
    if not url:
        return url
    # If already encrypted, avoid double encryption
    if url.startswith("enc:v1:"):
        return url

    try:
        nonce = os.urandom(12)
        ciphertext = _CIPHER.encrypt(nonce, url.encode("utf-8"), None)
        return f"enc:v1:{nonce.hex()}:{ciphertext.hex()}"
    except Exception as e:
        # On failure, return original (or None for safety)
        return url


def decrypt_media_url(token: Optional[str]) -> Optional[str]:
    """
    Decrypts an AES-256-GCM encrypted media link.
    """
    if not token or not token.startswith("enc:v1:"):
        return token

    try:
        parts = token.split(":")
        if len(parts) != 4:
            return token
        nonce = bytes.fromhex(parts[2])
        ciphertext = bytes.fromhex(parts[3])
        decrypted = _CIPHER.decrypt(nonce, ciphertext, None)
        return decrypted.decode("utf-8")
    except Exception:
        return token
