"""CloudMask - AWS Infrastructure Anonymizer.

Anonymize AWS resource IDs, account IDs, and other identifying information
for secure LLM processing while maintaining reversible mappings.
"""

from .__version__ import __version__
from .config_loader import load_config, load_from_env, validate_config
from .config_templates import get_template, list_templates, save_template
from .core import (
    CloudMask,
    CloudUnmask,
    Config,
    CustomPattern,
    TemporaryMask,
    anonymize,
    anonymize_dict,
    create_batch_anonymizer,
    unanonymize,
)
from .exceptions import (
    ClipboardError,
    CloudMaskError,
    ConfigurationError,
    EncryptionError,
    FileOperationError,
    MappingError,
    ValidationError,
)
from .logging import setup_logging
from .ratelimit import BatchRateLimiter, RateLimiter
from .security import (
    decrypt_mapping,
    encrypt_mapping,
    load_encrypted_mapping,
    save_encrypted_mapping,
)
from .streaming import stream_anonymize_file, stream_unanonymize_file

__all__ = [
    "BatchRateLimiter",
    "ClipboardError",
    "CloudMask",
    "CloudMaskError",
    "CloudUnmask",
    "Config",
    "ConfigurationError",
    "CustomPattern",
    "EncryptionError",
    "FileOperationError",
    "MappingError",
    "RateLimiter",
    "TemporaryMask",
    "ValidationError",
    "__version__",
    "anonymize",
    "anonymize_dict",
    "create_batch_anonymizer",
    "decrypt_mapping",
    "encrypt_mapping",
    "get_template",
    "list_templates",
    "load_config",
    "load_encrypted_mapping",
    "load_from_env",
    "save_encrypted_mapping",
    "save_template",
    "setup_logging",
    "stream_anonymize_file",
    "stream_unanonymize_file",
    "unanonymize",
    "validate_config",
]
