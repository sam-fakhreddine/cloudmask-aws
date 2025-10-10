"""File processing utilities."""

from collections.abc import Callable
from pathlib import Path

from ..exceptions import FileOperationError
from ..logging import log_operation, logger


class FileProcessor:
    """Handles file I/O operations."""

    MAX_FILE_SIZE = 100_000_000  # 100MB

    @staticmethod
    def read_file(filepath: Path) -> str:
        """Read file with validation."""
        if not filepath.exists():
            raise FileOperationError(
                f"Input file not found: {filepath}",
                "Check the file path and ensure the file exists",
            )

        file_size = filepath.stat().st_size
        if file_size > FileProcessor.MAX_FILE_SIZE:
            raise FileOperationError(
                f"File too large ({file_size / 1_000_000:.1f}MB, max 100MB)",
                "Use streaming for larger files or split the file",
            )

        try:
            return filepath.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise FileOperationError(
                f"Cannot read file (encoding error): {e}", "Ensure the file is UTF-8 encoded"
            ) from e

    @staticmethod
    def write_file(filepath: Path, content: str) -> None:
        """Write file with error handling."""
        try:
            filepath.write_text(content, encoding="utf-8")
        except OSError as e:
            raise FileOperationError(
                f"Cannot write to output file: {e}", "Check file permissions and disk space"
            ) from e

    @staticmethod
    def process_file(input_path: Path, output_path: Path, processor: Callable[[str], str]) -> int:
        """Process file with given processor function."""
        logger.debug(f"Processing file: {input_path} -> {output_path}")

        content = FileProcessor.read_file(input_path)
        processed = processor(content)
        FileProcessor.write_file(output_path, processed)

        log_operation(
            "file_processed",
            input=str(input_path),
            output=str(output_path),
        )
        return len(processed)
