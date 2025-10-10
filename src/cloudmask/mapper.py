"""Mapping file management."""

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .exceptions import FileOperationError, MappingError
from .io.storage import ensure_secure_permissions
from .logging import log_operation, logger


class MappingManager:
    """Manages mapping file operations."""

    def __init__(self, seed: str):
        """Initialize mapping manager with seed."""
        self.seed = seed
        self.mapping: dict[str, str] = {}

    def _get_seed_hash(self) -> str:
        """Get hash of current seed."""
        return hashlib.sha256(self.seed.encode()).hexdigest()[:16]

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
                payload["mappings"] = {**existing.get("mappings", {}), **self.mapping}
                logger.debug(f"Merged {len(existing.get('mappings', {}))} existing mappings")
            else:
                logger.warning("Existing mapping has no seed metadata")
                payload["mappings"] = {**existing, **self.mapping}

        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not load existing mapping: {e}")

    def _write_atomic(self, filepath: Path, data: dict[str, Any]) -> None:
        """Write mapping file atomically."""
        temp_fd, temp_path = tempfile.mkstemp(
            dir=filepath.parent, prefix=".cloudmask_", suffix=".tmp"
        )
        temp_file = Path(temp_path)

        try:
            with temp_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.close(temp_fd)
            ensure_secure_permissions(temp_file)
            temp_file.replace(filepath)
        except Exception:
            temp_file.unlink(missing_ok=True)
            raise

    def save(self, filepath: Path, merge: bool = True) -> None:
        """Save mapping to file."""
        logger.debug(f"Saving mapping to {filepath}")

        payload = self._build_payload()

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
                f"Cannot write mapping file: {e}", "Check file permissions and disk space"
            ) from e

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
