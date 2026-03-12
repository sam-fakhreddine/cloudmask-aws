"""Mapping file management."""

import fcntl
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .exceptions import FileOperationError, MappingError
from .logging import log_operation, logger


class MappingManager:
    """Manages mapping file operations."""

    def __init__(self, seed: str):
        """Initialize mapping manager with seed."""
        self.seed = seed
        self.mapping: dict[str, str] = {}
        self._seed_hash = hashlib.sha256(seed.encode()).hexdigest()[:16] if seed else ""

    def _get_seed_hash(self) -> str:
        """Get hash of current seed."""
        return self._seed_hash

    def _build_payload(self) -> dict[str, Any]:
        """Build mapping payload with metadata."""
        return {
            "_metadata": {
                "seed_hash": self._get_seed_hash(),
                "version": "1.0",
            },
            "mappings": self.mapping,
        }

    def _merge_existing(self, filepath: Path, payload: dict[str, Any]) -> None:
        """Merge with existing mappings if file exists."""
        try:
            if not filepath.exists():
                return
        except (OSError, PermissionError):
            return

        try:
            existing = json.loads(filepath.read_text(encoding="utf-8"))

            if "_metadata" in existing:
                if existing["_metadata"].get("seed_hash") != payload["_metadata"]["seed_hash"]:
                    raise MappingError(
                        "Cannot merge mappings created with different seeds",
                        "Use the same seed for all mappings",
                    )
                existing_mappings = existing.get("mappings", {})
                existing_mappings.update(self.mapping)
                payload["mappings"] = existing_mappings
                logger.debug(f"Merged {len(existing.get('mappings', {}))} existing mappings")
            else:
                logger.warning("Existing mapping has no seed metadata")
                existing.update(self.mapping)
                payload["mappings"] = existing

        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not load existing mapping: {e}")

    def _write_atomic(self, filepath: Path, data: dict[str, Any]) -> None:
        """Write mapping file atomically."""
        temp_fd, temp_path = tempfile.mkstemp(
            dir=filepath.parent, prefix=".cloudmask_", suffix=".tmp"
        )
        temp_file = Path(temp_path)

        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, separators=(",", ":"))
            temp_file.chmod(0o600)
            temp_file.replace(filepath)
        except Exception:
            temp_file.unlink(missing_ok=True)
            raise

    def _save_inner(self, filepath: Path, payload: dict[str, Any], merge: bool) -> None:
        """Execute the merge-check-write cycle (caller holds any lock)."""
        if merge:
            self._merge_existing(filepath, payload)

        if len(payload["mappings"]) > 1_000_000:
            raise MappingError(
                f"Mapping too large ({len(payload['mappings'])} entries)",
                "Process data in smaller batches",
            )

        try:
            self._write_atomic(filepath, payload)
        except OSError as e:
            raise FileOperationError(
                f"Cannot write mapping file: {e}",
                "Check file permissions and disk space",
            ) from e

    def _acquire_lock(self, filepath: Path):
        """Acquire file lock, returning lock file or None on failure."""
        lock_path = filepath.with_suffix(".lock")
        try:
            lock_file = lock_path.open("w")
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            return lock_file
        except OSError as e:
            logger.warning(f"Could not acquire lock ({e}), proceeding without lock")
            return None

    def _release_lock(self, lock_file) -> None:
        """Release file lock."""
        if lock_file is not None:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
            except OSError:
                pass

    def save(self, filepath: Path, merge: bool = True) -> None:
        """Save mapping to file."""
        logger.debug(f"Saving mapping to {filepath}")

        payload = self._build_payload()
        filepath.parent.mkdir(parents=True, exist_ok=True)

        lock_file = self._acquire_lock(filepath)
        try:
            self._save_inner(filepath, payload, merge)
        finally:
            self._release_lock(lock_file)

        log_operation("mapping_saved", path=str(filepath), entries=len(payload["mappings"]))

    def load(self, filepath: Path) -> None:
        """Load mapping from file."""
        logger.debug(f"Loading mapping from {filepath}")

        if not filepath.exists():
            raise FileOperationError(
                f"Mapping file not found: {filepath}",
                "Ensure you have saved the mapping file during anonymization",
            )

        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise MappingError(
                f"Invalid JSON in mapping file: {e}", "Ensure the mapping file is valid JSON"
            ) from e

        if "_metadata" in data and "mappings" in data:
            if data["_metadata"].get("seed_hash") != self._get_seed_hash():
                raise MappingError(
                    "Mapping was created with a different seed",
                    "Use the same seed that was used to create the mapping",
                )
            mapping = data["mappings"]
        else:
            logger.warning("Loading mapping without seed verification (old format)")
            mapping = data

        if not isinstance(mapping, dict):
            raise MappingError(
                "Mapping file must contain a JSON object",
                "The mapping file should be a dictionary",
            )

        self.mapping = mapping
        log_operation("mapping_loaded", path=str(filepath), entries=len(mapping))
