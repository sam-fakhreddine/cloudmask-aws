"""CloudMask - AWS Infrastructure Anonymizer."""

from .__version__ import __version__
from .config.config import Config, CustomPattern
from .core import (
    CloudMask,
    CloudUnmask,
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
from .io.file_processor import FileProcessor
from .logging import log_operation, logger, setup_logging

_LAZY_IMPORTS = {
    "load_config": ".config.config_loader",
    "load_from_env": ".config.config_loader",
    "validate_config": ".config.config_loader",
    "ConfigTemplates": ".config.config_templates",
    "get_template": ".config.config_templates",
    "list_templates": ".config.config_templates",
    "save_template": ".config.config_templates",
    "Storage": ".io.storage",
    "ensure_secure_permissions": ".io.storage",
    "get_default_config_path": ".io.storage",
    "get_default_mapping_path": ".io.storage",
    "get_storage_dir": ".io.storage",
    "stream_anonymize_file": ".io.streaming",
    "stream_unanonymize_file": ".io.streaming",
    "BatchRateLimiter": ".utils.ratelimit",
    "RateLimiter": ".utils.ratelimit",
    "decrypt_mapping": ".utils.security",
    "encrypt_mapping": ".utils.security",
    "load_encrypted_mapping": ".utils.security",
    "save_encrypted_mapping": ".utils.security",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name], __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module 'cloudmask' has no attribute {name!r}")


__all__ = [
    "__version__",
    "Config",
    "CustomPattern",
    "CloudMask",
    "CloudUnmask",
    "TemporaryMask",
    "anonymize",
    "anonymize_dict",
    "create_batch_anonymizer",
    "unanonymize",
    "ClipboardError",
    "CloudMaskError",
    "ConfigurationError",
    "EncryptionError",
    "FileOperationError",
    "MappingError",
    "ValidationError",
    "FileProcessor",
    "log_operation",
    "logger",
    "setup_logging",
    *_LAZY_IMPORTS.keys(),
]
