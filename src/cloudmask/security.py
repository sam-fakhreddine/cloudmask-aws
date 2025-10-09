"""Security utilities for CloudMask."""

import base64
import hashlib
import json
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .exceptions import EncryptionError, FileOperationError, ValidationError
from .logging import logger


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive encryption key from password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt_mapping(mapping: dict[str, str], password: str) -> bytes:
    """Encrypt mapping dictionary with password."""
    if not password or len(password) < 8:
        raise ValidationError(
            "Password must be at least 8 characters", "Use a strong password for encryption"
        )

    salt = hashlib.sha256(password.encode()).digest()[:16]
    key = derive_key(password, salt)
    fernet = Fernet(key)

    data = json.dumps(mapping).encode()
    encrypted_bytes: bytes = fernet.encrypt(data)

    return salt + encrypted_bytes


def decrypt_mapping(encrypted_data: bytes, password: str) -> dict[str, str]:
    """Decrypt mapping dictionary with password."""
    if len(encrypted_data) < 16:
        raise EncryptionError(
            "Invalid encrypted data", "Ensure the file is a valid encrypted mapping file"
        )

    salt = encrypted_data[:16]
    encrypted = encrypted_data[16:]

    key = derive_key(password, salt)
    fernet = Fernet(key)

    try:
        decrypted = fernet.decrypt(encrypted)
        return json.loads(decrypted.decode())  # type: ignore[no-any-return]
    except Exception as e:
        raise EncryptionError(
            "Decryption failed. Invalid password or corrupted data",
            "Verify your password and ensure the file is not corrupted",
        ) from e


def save_encrypted_mapping(mapping: dict[str, str], filepath: Path, password: str) -> None:
    """Save encrypted mapping to file."""
    logger.debug(f"Saving encrypted mapping to {filepath}")
    encrypted = encrypt_mapping(mapping, password)
    try:
        filepath.write_bytes(encrypted)
    except OSError as e:
        raise FileOperationError(
            f"Cannot write encrypted mapping: {e}", "Check file permissions and disk space"
        ) from e


def load_encrypted_mapping(filepath: Path, password: str) -> dict[str, str]:
    """Load encrypted mapping from file."""
    logger.debug(f"Loading encrypted mapping from {filepath}")

    if not filepath.exists():
        raise FileOperationError(
            f"Mapping file not found: {filepath}",
            "Ensure you have saved the encrypted mapping file",
        )

    try:
        encrypted = filepath.read_bytes()
    except OSError as e:
        raise FileOperationError(
            f"Cannot read encrypted mapping: {e}", "Check file permissions"
        ) from e

    return decrypt_mapping(encrypted, password)
