"""Encryption utilities for sensitive data.

Uses Fernet symmetric encryption from the cryptography library
for encrypting OAuth tokens and PDF passwords.
"""

import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""

    pass


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    """Get Fernet instance with the encryption key from environment.

    Caches the instance for performance.
    Raises EncryptionError if key is not configured or invalid.
    """
    key = os.environ.get("GMAIL_ENCRYPTION_KEY")
    if not key:
        raise EncryptionError(
            "GMAIL_ENCRYPTION_KEY environment variable is not set. "
            'Generate a key with: python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        )

    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError) as e:
        raise EncryptionError(f"Invalid GMAIL_ENCRYPTION_KEY: {e}") from e


def encrypt(plaintext: str) -> str:
    """Encrypt a string using Fernet symmetric encryption.

    Args:
        plaintext: The string to encrypt.

    Returns:
        Base64-encoded encrypted string.

    Raises:
        EncryptionError: If encryption fails or key is not configured.
    """
    if not plaintext:
        raise EncryptionError("Cannot encrypt empty string")

    try:
        fernet = _get_fernet()
        encrypted = fernet.encrypt(plaintext.encode("utf-8"))
        return encrypted.decode("utf-8")
    except Exception as e:
        if isinstance(e, EncryptionError):
            raise
        raise EncryptionError(f"Encryption failed: {e}") from e


def decrypt(ciphertext: str) -> str:
    """Decrypt a Fernet-encrypted string.

    Args:
        ciphertext: Base64-encoded encrypted string.

    Returns:
        The decrypted plaintext string.

    Raises:
        EncryptionError: If decryption fails or key is not configured.
    """
    if not ciphertext:
        raise EncryptionError("Cannot decrypt empty string")

    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(ciphertext.encode("utf-8"))
        return decrypted.decode("utf-8")
    except InvalidToken as e:
        raise EncryptionError(
            "Decryption failed: invalid token. "
            "This may indicate the data was encrypted with a different key."
        ) from e
    except Exception as e:
        if isinstance(e, EncryptionError):
            raise
        raise EncryptionError(f"Decryption failed: {e}") from e


def generate_key() -> str:
    """Generate a new Fernet encryption key.

    Returns:
        A base64-encoded 32-byte key suitable for GMAIL_ENCRYPTION_KEY.
    """
    return Fernet.generate_key().decode("utf-8")
