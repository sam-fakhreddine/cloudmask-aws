"""Custom exceptions for CloudMask."""


class CloudMaskError(Exception):
    """Base exception for all CloudMask errors."""

    def __init__(self, message: str, suggestion: str | None = None) -> None:
        """Initialize with message and optional suggestion."""
        self.message = message
        self.suggestion = suggestion
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format error message with suggestion."""
        if self.suggestion:
            return f"{self.message}\n💡 Suggestion: {self.suggestion}"
        return self.message


class ConfigurationError(CloudMaskError):
    """Configuration-related errors."""


class ValidationError(CloudMaskError):
    """Input validation errors."""


class FileOperationError(CloudMaskError):
    """File operation errors."""


class MappingError(CloudMaskError):
    """Mapping-related errors."""


class EncryptionError(CloudMaskError):
    """Encryption/decryption errors."""


class ClipboardError(CloudMaskError):
    """Clipboard operation errors."""
