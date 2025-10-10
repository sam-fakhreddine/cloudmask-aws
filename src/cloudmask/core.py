"""CloudMask - Refactored core module."""

__version__ = "0.2.0"

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .anonymizer import Anonymizer
from .config.config import Config
from .io.file_processor import FileProcessor
from .logging import logger
from .mapper import MappingManager


class CloudMask:
    """Main anonymizer class."""

    def __init__(self, config: Config | None = None, seed: str | None = None):
        """Initialize CloudMask with configuration and seed."""
        self.config = config or Config()
        self.seed = seed or self.config.seed
        self._anonymizer = Anonymizer(self.config, self.seed)
        self._mapper = MappingManager(self.seed)

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
            case (None, Path() as f):
                logger.debug(f"Loading mapping from {f}")
                import json

                from .exceptions import FileOperationError, MappingError

                if not f.exists():
                    raise FileOperationError(
                        f"Mapping file not found: {f}",
                        "Ensure you have saved the mapping file during anonymization",
                    )
                try:
                    data = json.loads(f.read_text())
                    loaded = data.get("mappings", data) if "_metadata" in data else data
                    self.reverse_mapping = {v: k for k, v in loaded.items()}
                except json.JSONDecodeError as e:
                    raise MappingError(
                        f"Invalid JSON in mapping file: {e}",
                        "Ensure the mapping file is valid JSON",
                    ) from e
            case (None, None):
                logger.debug("Initializing with empty mapping")
                self.reverse_mapping = {}
            case _:
                from .exceptions import ValidationError

                raise ValidationError(
                    "Provide either mapping or mapping_file, not both",
                    "Use only one parameter",
                )

    def unanonymize(self, text: str) -> str:
        """Restore original values."""
        result = text
        for anonymized, original in sorted(
            self.reverse_mapping.items(), key=lambda x: len(x[0]), reverse=True
        ):
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
        """Exit context and cleanup."""
        pass


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


def anonymize_dict(data: dict[str, Any], mask: CloudMask) -> dict[str, Any]:
    """Recursively anonymize dictionary values."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        match value:
            case str():
                result[key] = mask.anonymize(value)
            case dict():
                result[key] = anonymize_dict(value, mask)
            case list():
                result[key] = [
                    (
                        mask.anonymize(item)
                        if isinstance(item, str)
                        else anonymize_dict(item, mask) if isinstance(item, dict) else item
                    )
                    for item in value
                ]
            case _:
                result[key] = value
    return result
