"""CloudMask - Refactored core module."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .anonymizer import Anonymizer
from .config.config import Config
from .exceptions import FileOperationError, MappingError, ValidationError
from .io.file_processor import FileProcessor
from .logging import logger
from .mapper import MappingManager


class CloudMask:
    """Main anonymizer class."""

    def __init__(self, config: Config | None = None, seed: str | None = None):
        """Initialize CloudMask with configuration and seed."""
        self.config = config or Config()
        self.seed = seed if seed is not None else self.config.seed
        self._anonymizer = Anonymizer(self.config, self.seed)
        self._mapper = MappingManager(self.seed)
        # Share the same mapping dict so save/load are always in sync
        self._mapper.mapping = self._anonymizer.mapping

    @property
    def mapping(self) -> dict[str, str]:
        """Get current mapping."""
        return self._anonymizer.mapping

    def anonymize(self, text: str) -> str:
        """Anonymize text."""
        return self._anonymizer.anonymize(text)

    def anonymize_file(self, input_path: Path, output_path: Path) -> int:
        """Anonymize a file."""
        FileProcessor.process_file(input_path, output_path, self.anonymize)
        return len(self.mapping)

    def save_mapping(self, filepath: Path | str, merge: bool = True) -> None:
        """Save mapping to file."""
        filepath = Path(filepath) if isinstance(filepath, str) else filepath
        self._mapper.mapping = self.mapping
        self._mapper.save(filepath, merge)

    def load_mapping(self, filepath: Path | str) -> None:
        """Load mapping from file."""
        filepath = Path(filepath) if isinstance(filepath, str) else filepath
        self._mapper.load(filepath)
        self._anonymizer.mapping = self._mapper.mapping

    def get_mapping(self) -> dict[str, str]:
        """Get copy of current mapping."""
        return self.mapping.copy()


class CloudUnmask:
    """Unanonymizer class."""

    def __init__(self, mapping: dict[str, str] | None = None, mapping_file: Path | None = None):
        """Initialize CloudUnmask with mapping or mapping file."""
        match (mapping, mapping_file):
            case (dict() as m, None):
                logger.debug("Initializing with provided mapping")
                self.reverse_mapping = {v: k for k, v in m.items()}
                self._sorted_replacements = sorted(
                    self.reverse_mapping.items(), key=lambda x: len(x[0]), reverse=True
                )
            case (None, Path() as f):
                logger.debug(f"Loading mapping from {f}")
                if not f.exists():
                    raise FileOperationError(
                        f"Mapping file not found: {f}",
                        "Ensure you have saved the mapping file during anonymization",
                    )
                try:
                    data = json.loads(f.read_text())
                    loaded = data.get("mappings", data) if "_metadata" in data else data
                    self.reverse_mapping = {v: k for k, v in loaded.items()}
                    self._sorted_replacements = sorted(
                        self.reverse_mapping.items(), key=lambda x: len(x[0]), reverse=True
                    )
                except json.JSONDecodeError as e:
                    raise MappingError(
                        f"Invalid JSON in mapping file: {e}",
                        "Ensure the mapping file is valid JSON",
                    ) from e
            case (None, None):
                logger.debug("Initializing with empty mapping")
                self.reverse_mapping = {}
                self._sorted_replacements = []
            case _:
                raise ValidationError(
                    "Provide either mapping or mapping_file, not both",
                    "Use only one parameter",
                )

    def unanonymize(self, text: str) -> str:
        """Restore original values."""
        result = text
        for anonymized, original in self._sorted_replacements:
            result = result.replace(anonymized, original)
        return result

    def unanonymize_file(self, input_path: Path, output_path: Path) -> int:
        """Unanonymize a file."""
        FileProcessor.process_file(input_path, output_path, self.unanonymize)
        return len(self.reverse_mapping)


class TemporaryMask:
    """Context manager for temporary anonymization."""

    def __init__(self, seed: str | None = None, config: Config | None = None):
        """Initialize temporary mask."""
        self.seed = seed
        self.config = config
        self.mask: CloudMask | None = None

    def __enter__(self) -> CloudMask:
        """Enter context and create CloudMask instance."""
        self.mask = CloudMask(config=self.config, seed=self.seed)
        return self.mask

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and clear sensitive mapping data."""
        if self.mask is not None:
            self.mask._anonymizer.mapping.clear()
            self.mask._mapper.mapping.clear()
            self.mask = None


def anonymize(
    text: str, seed: str = "default-seed", **config_options: Any
) -> tuple[str, dict[str, str]]:
    """Quick anonymization function."""
    config = Config(seed=seed, **config_options)
    mask = CloudMask(config=config)
    anonymized = mask.anonymize(text)
    return anonymized, mask.get_mapping()


def unanonymize(text: str, mapping: dict[str, str]) -> str:
    """Quick unanonymization function."""
    unmask = CloudUnmask(mapping=mapping)
    return unmask.unanonymize(text)


def create_batch_anonymizer(seed: str, config: Config | None = None) -> Callable[[str], str]:
    """Create a reusable anonymization function."""
    mask = CloudMask(config=config, seed=seed)
    return mask.anonymize


def _anonymize_value(value: Any, mask: CloudMask) -> Any:
    """Recursively anonymize a value."""
    match value:
        case str():
            return mask.anonymize(value)
        case dict():
            return anonymize_dict(value, mask)
        case list():
            return [_anonymize_value(item, mask) for item in value]
        case _:
            return value


def anonymize_dict(data: dict[str, Any], mask: CloudMask) -> dict[str, Any]:
    """Recursively anonymize dictionary values (keys preserved as-is)."""
    return {key: _anonymize_value(value, mask) for key, value in data.items()}
