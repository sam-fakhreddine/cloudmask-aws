"""Streaming support for large file processing."""

from collections.abc import Iterator
from pathlib import Path
from typing import TextIO

from .core import CloudMask, CloudUnmask
from .exceptions import FileOperationError
from .logging import logger


def stream_anonymize_file(
    mask: CloudMask,
    input_path: Path,
    output_path: Path,
    chunk_size: int = 8192,
    show_progress: bool = False,
) -> int:
    """Stream-process large files for memory efficiency.

    Args:
        mask: CloudMask instance
        input_path: Input file path
        output_path: Output file path
        chunk_size: Bytes to read per chunk
        show_progress: Show progress bar

    Returns:
        Number of unique identifiers anonymized
    """
    if not input_path.exists():
        raise FileOperationError(
            f"Input file not found: {input_path}", "Check the file path and ensure the file exists"
        )

    file_size = input_path.stat().st_size
    logger.debug(f"Streaming file: {input_path} ({file_size} bytes)")

    progress_bar = None
    if show_progress:
        try:
            from tqdm import tqdm

            progress_bar = tqdm(total=file_size, unit="B", unit_scale=True, desc="Anonymizing")
        except ImportError:
            logger.warning("tqdm not available, progress bar disabled")

    try:
        with (
            input_path.open("r", encoding="utf-8") as infile,
            output_path.open("w", encoding="utf-8") as outfile,
        ):

            for chunk in _read_chunks(infile, chunk_size):
                anonymized = mask.anonymize(chunk)
                outfile.write(anonymized)

                if progress_bar:
                    progress_bar.update(len(chunk.encode("utf-8")))

        if progress_bar:
            progress_bar.close()

    except UnicodeDecodeError as e:
        raise FileOperationError(
            f"Cannot read file (encoding error): {e}", "Ensure the file is UTF-8 encoded"
        ) from e
    except OSError as e:
        raise FileOperationError(
            f"File operation failed: {e}", "Check file permissions and disk space"
        ) from e

    return len(mask.mapping)


def stream_unanonymize_file(
    unmask: CloudUnmask,
    input_path: Path,
    output_path: Path,
    chunk_size: int = 8192,
    show_progress: bool = False,
) -> int:
    """Stream-process large files for unanonymization.

    Args:
        unmask: CloudUnmask instance
        input_path: Input file path
        output_path: Output file path
        chunk_size: Bytes to read per chunk
        show_progress: Show progress bar

    Returns:
        Number of identifiers restored
    """
    if not input_path.exists():
        raise FileOperationError(
            f"Input file not found: {input_path}", "Check the file path and ensure the file exists"
        )

    file_size = input_path.stat().st_size
    logger.debug(f"Streaming file: {input_path} ({file_size} bytes)")

    progress_bar = None
    if show_progress:
        try:
            from tqdm import tqdm

            progress_bar = tqdm(total=file_size, unit="B", unit_scale=True, desc="Unanonymizing")
        except ImportError:
            logger.warning("tqdm not available, progress bar disabled")

    try:
        with (
            input_path.open("r", encoding="utf-8") as infile,
            output_path.open("w", encoding="utf-8") as outfile,
        ):

            for chunk in _read_chunks(infile, chunk_size):
                unanonymized = unmask.unanonymize(chunk)
                outfile.write(unanonymized)

                if progress_bar:
                    progress_bar.update(len(chunk.encode("utf-8")))

        if progress_bar:
            progress_bar.close()

    except UnicodeDecodeError as e:
        raise FileOperationError(
            f"Cannot read file (encoding error): {e}", "Ensure the file is UTF-8 encoded"
        ) from e
    except OSError as e:
        raise FileOperationError(
            f"File operation failed: {e}", "Check file permissions and disk space"
        ) from e

    return len(unmask.reverse_mapping)


def _read_chunks(file: TextIO, chunk_size: int) -> Iterator[str]:
    """Read file in chunks."""
    while True:
        chunk = file.read(chunk_size)
        if not chunk:
            break
        yield chunk
