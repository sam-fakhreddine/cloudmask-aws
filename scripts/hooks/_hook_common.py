"""Shared utilities for CloudMask Claude Code hooks.

Provides seed resolution, Fernet encryption/decryption with cached PBKDF2 key
derivation, and hook response helpers.  Imported by both mask-hook.py and
demask-hook.py so that seed reading, crypto, and constants are defined once.
"""

import hashlib
import json
import os
import sys
from functools import lru_cache
from pathlib import Path

SHADOW_ROOT = Path.home() / ".cloudmask" / "hooks" / "shadow"
MAPPING_PATH = Path.home() / ".cloudmask" / "hooks" / "mapping.json"
SEED_FILE = Path.home() / ".cloudmask" / "seed"

# Marker line embedded in sanitized files to prevent double anonymization
CLOUDMASK_MARKER = "<!-- CLOUDMASK:SANITIZED -->"


def read_seed() -> str:
    """Read seed: OS keychain -> dedicated file -> env var."""
    try:
        import keyring

        seed = keyring.get_password("cloudmask", "seed")
        if seed:
            return seed
    except Exception:
        pass
    try:
        if SEED_FILE.is_file():
            seed = SEED_FILE.read_text(encoding="utf-8").strip()
            if seed:
                return seed
    except OSError:
        pass
    return os.environ.get("CLOUDMASK_SEED", "")


@lru_cache(maxsize=1)
def _cached_fernet(seed: str) -> tuple:
    """Derive and cache Fernet key with deterministic salt.

    Uses a deterministic salt derived from the seed hash, so PBKDF2
    (100K iterations) runs only once per process — not per operation.
    """
    import base64

    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    salt = hashlib.sha256(seed.encode()).digest()[:16]
    key = base64.urlsafe_b64encode(
        PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000).derive(
            seed.encode()
        )
    )
    return salt, Fernet(key)


def _derive_fernet_for_salt(salt: bytes, seed: str):  # type: ignore[return]
    """Derive Fernet for a specific (legacy random) salt — uncached."""
    import base64

    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    key = base64.urlsafe_b64encode(
        PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000).derive(
            seed.encode()
        )
    )
    return Fernet(key)


def encrypt_json(data: dict, seed: str) -> bytes:
    """Encrypt dict as JSON using Fernet with cached PBKDF2-derived key."""
    salt, fernet = _cached_fernet(seed)
    return salt + fernet.encrypt(json.dumps(data, separators=(",", ":")).encode())


def decrypt_json(blob: bytes, seed: str) -> dict:
    """Decrypt Fernet-encrypted JSON.  Handles deterministic and legacy random salt."""
    file_salt = blob[:16]
    cached_salt, cached_fernet = _cached_fernet(seed)

    fernet = cached_fernet if file_salt == cached_salt else _derive_fernet_for_salt(file_salt, seed)
    return json.loads(fernet.decrypt(blob[16:]))


def load_mapping_data(seed: str) -> dict:
    """Load mapping from encrypted or plaintext file."""
    if not MAPPING_PATH.exists():
        return {}
    try:
        raw = MAPPING_PATH.read_bytes()
        if not raw:
            return {}
    except OSError:
        return {}
    try:
        return decrypt_json(raw, seed)
    except Exception:
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}


def save_mapping_encrypted(mapping: dict[str, str], seed: str) -> None:
    """Save mapping as encrypted file with metadata."""
    import tempfile

    payload = {
        "_metadata": {
            "seed_hash": hashlib.sha256(seed.encode()).hexdigest()[:16],
            "version": "1.0",
        },
        "mappings": dict(mapping),
    }
    try:
        file_data = encrypt_json(payload, seed)
    except ImportError:
        file_data = json.dumps(payload, separators=(",", ":")).encode()
    MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=MAPPING_PATH.parent, prefix=".mask_", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(file_data)
        Path(tmp).chmod(0o600)
        Path(tmp).replace(MAPPING_PATH)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def block_tool(reason: str) -> None:
    """Emit a PreToolUse block decision to stdout."""
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "block",
                "reason": reason,
            }
        },
        sys.stdout,
    )
