---
title: Fix All 55 Review Findings
status: active
created: 2026-03-11T11:00:00Z
updated: 2026-03-11T11:00:00Z
tasks_total: 45
tasks_completed: 0
---

# TASKS: Fix All 55 WFC Review Findings

8 parallel file chains. Tasks within the same file are sequential (dependency chain).
Cross-file dependencies noted where they exist.

---

## Chain A: src/cloudmask/utils/patterns.py (1 task)

### TASK-001: Extract AWS_RESOURCE_PREFIXES constant
- **Complexity**: S
- **Dependencies**: []
- **Canary**: true
- **Files**: [src/cloudmask/utils/patterns.py]
- **Findings**: Maintainability #16, #17 (duplicated prefix list in 3 locations)

**Find** (line 11-14):
```python
AWS_RESOURCE_PATTERN = re.compile(
    r"\b(vpc|subnet|sg|igw|rtb|eni|eip|vol|snap|ami|i|r|lt|asg|elb|tg|elbv2|"
    r"natgw|vpce|acl|pcx|vgw|cgw|vpn|dopt|nacl)-(?:[0-9a-z]{3}(?![0-9a-z])|[0-9a-f]{4,17})\b",
    re.IGNORECASE,
)
```

**Replace**:
```python
AWS_RESOURCE_PREFIXES = frozenset({
    "vpc", "subnet", "sg", "igw", "rtb", "eni", "eip", "vol", "snap",
    "ami", "i", "r", "lt", "asg", "elb", "tg", "elbv2", "natgw",
    "vpce", "acl", "pcx", "vgw", "cgw", "vpn", "dopt", "nacl",
})

_PREFIX_ALT = "|".join(sorted(AWS_RESOURCE_PREFIXES, key=len, reverse=True))

AWS_RESOURCE_PATTERN = re.compile(
    rf"\b({_PREFIX_ALT})-(?:[0-9a-z]{{3}}(?![0-9a-z])|[0-9a-f]{{4,17}})\b",
    re.IGNORECASE,
)
```

- **Acceptance Criteria**:
  - [ ] `grep -c "AWS_RESOURCE_PREFIXES" src/cloudmask/utils/patterns.py` returns >= 1
  - [ ] `grep -c "frozenset" src/cloudmask/utils/patterns.py` returns >= 1
  - [ ] `python -c "from cloudmask.utils.patterns import AWS_RESOURCE_PREFIXES; assert len(AWS_RESOURCE_PREFIXES) == 25"` exits 0

---

## Chain B: src/cloudmask/__init__.py (1 task)

### TASK-002: Convert eager imports to lazy __getattr__
- **Complexity**: L
- **Dependencies**: []
- **Canary**: false
- **Files**: [src/cloudmask/__init__.py]
- **Findings**: Performance #14 (130-380ms import overhead), Critical #4

**Find** (full file, lines 1-91): Replace the entire file contents.

**Replace**: Keep only core imports eager; defer heavy modules via `__getattr__`:
```python
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

__all__ = [
    "BatchRateLimiter",
    "ClipboardError",
    "CloudMask",
    "CloudMaskError",
    "CloudUnmask",
    "Config",
    "ConfigTemplates",
    "ConfigurationError",
    "CustomPattern",
    "EncryptionError",
    "FileOperationError",
    "MappingError",
    "RateLimiter",
    "Storage",
    "TemporaryMask",
    "ValidationError",
    "__version__",
    "anonymize",
    "anonymize_dict",
    "create_batch_anonymizer",
    "decrypt_mapping",
    "encrypt_mapping",
    "ensure_secure_permissions",
    "get_default_config_path",
    "get_default_mapping_path",
    "get_storage_dir",
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
    "setup_logging": ".logging",
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
```

- **Acceptance Criteria**:
  - [ ] `grep -c "__getattr__" src/cloudmask/__init__.py` returns 1
  - [ ] `grep -c "_LAZY_IMPORTS" src/cloudmask/__init__.py` returns >= 2
  - [ ] `python -c "from cloudmask import CloudMask; print('ok')"` exits 0
  - [ ] `python -c "from cloudmask import encrypt_mapping; print('ok')"` exits 0
  - [ ] `grep -c "from .utils.security" src/cloudmask/__init__.py` returns 0
  - [ ] `grep -c "from .config.config_loader" src/cloudmask/__init__.py` returns 0

---

## Chain C: src/cloudmask/config/config.py (1 task)

### TASK-003: Add DEFAULT_SEED constant and warn on weak seed
- **Complexity**: S
- **Dependencies**: []
- **Canary**: false
- **Files**: [src/cloudmask/config/config.py]
- **Findings**: Maintainability #18 (3 different default seeds), Security #15 (default seed)

**Find** (line 42):
```python
    seed: str = "default-seed"
```

**Replace**:
```python
    seed: str = "default-seed"

    # Canonical default — referenced by hooks and convenience functions
    DEFAULT_SEED = "default-seed"
```

Also **find** (line 44-54):
```python
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not isinstance(self.company_names, list):
            raise ConfigurationError(
                "company_names must be a list", "Use: company_names: ['Company1', 'Company2']"
            )
        if not isinstance(self.custom_patterns, list):
            raise ConfigurationError(
                "custom_patterns must be a list",
                "Use: custom_patterns: [{pattern: '...', name: '...'}]",
            )
```

**Replace**:
```python
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not isinstance(self.company_names, list):
            raise ConfigurationError(
                "company_names must be a list", "Use: company_names: ['Company1', 'Company2']"
            )
        if not isinstance(self.custom_patterns, list):
            raise ConfigurationError(
                "custom_patterns must be a list",
                "Use: custom_patterns: [{pattern: '...', name: '...'}]",
            )
        if self.seed == self.DEFAULT_SEED:
            import warnings
            warnings.warn(
                "Using default seed. Set a unique seed for production use.",
                stacklevel=2,
            )
```

- **Acceptance Criteria**:
  - [ ] `grep -c "DEFAULT_SEED" src/cloudmask/config/config.py` returns >= 2
  - [ ] `grep -c "warnings.warn" src/cloudmask/config/config.py` returns 1

---

## Chain D: src/cloudmask/anonymizer.py (7 tasks, sequential)

### TASK-004: Move AWS_RESOURCE_PATTERN import to top level
- **Complexity**: S
- **Dependencies**: []
- **Canary**: false
- **Files**: [src/cloudmask/anonymizer.py]
- **Findings**: Maintainability #6 (deferred import), Performance #6 (import in callback)

**Find** (line 7-13):
```python
from .utils.patterns import (
    AWS_ACCOUNT_PATTERN,
    DOMAIN_PATTERN,
    IP_ADDRESS_PATTERN,
    get_aws_patterns,
    is_valid_ip,
)
```

**Replace**:
```python
from .utils.patterns import (
    AWS_ACCOUNT_PATTERN,
    AWS_RESOURCE_PATTERN,
    DOMAIN_PATTERN,
    IP_ADDRESS_PATTERN,
    get_aws_patterns,
    is_valid_ip,
)
```

Also **find** (line 129-130):
```python
            from .utils.patterns import AWS_RESOURCE_PATTERN
            result = AWS_RESOURCE_PATTERN.sub(lambda m: self._anonymize_aws_resource(m), result)
```

**Replace**:
```python
            result = AWS_RESOURCE_PATTERN.sub(lambda m: self._anonymize_aws_resource(m), result)
```

- **Acceptance Criteria**:
  - [ ] `grep -c "AWS_RESOURCE_PATTERN" src/cloudmask/anonymizer.py` returns >= 2
  - [ ] `grep -c "from .utils.patterns import AWS_RESOURCE_PATTERN" src/cloudmask/anonymizer.py` returns 0

---

### TASK-005: Extract _KNOWN_PREFIXES to class constant from patterns module
- **Complexity**: S
- **Dependencies**: [TASK-001, TASK-004]
- **Canary**: false
- **Files**: [src/cloudmask/anonymizer.py]
- **Findings**: Performance #7 (set re-allocated per call), Maintainability #5 (duplicated set)

**Find** (line 7-13 after TASK-004):
```python
from .utils.patterns import (
    AWS_ACCOUNT_PATTERN,
    AWS_RESOURCE_PATTERN,
    DOMAIN_PATTERN,
    IP_ADDRESS_PATTERN,
    get_aws_patterns,
    is_valid_ip,
)
```

**Replace**:
```python
from .utils.patterns import (
    AWS_ACCOUNT_PATTERN,
    AWS_RESOURCE_PATTERN,
    AWS_RESOURCE_PREFIXES,
    DOMAIN_PATTERN,
    IP_ADDRESS_PATTERN,
    get_aws_patterns,
    is_valid_ip,
)
```

Also **find** (lines 84-117, the _extract_prefix method):
```python
    def _extract_prefix(self, resource_id: str) -> str:
        """Extract AWS resource prefix."""
        if "-" not in resource_id:
            return ""
        prefix = resource_id.split("-", 1)[0]
        known = {
            "vpc",
            "subnet",
            "sg",
            "igw",
            "rtb",
            "eni",
            "eip",
            "vol",
            "snap",
            "ami",
            "i",
            "r",
            "lt",
            "asg",
            "elb",
            "tg",
            "elbv2",
            "natgw",
            "vpce",
            "acl",
            "pcx",
            "vgw",
            "cgw",
            "vpn",
            "dopt",
            "nacl",
        }
        return prefix if prefix in known else ""
```

**Replace**:
```python
    def _extract_prefix(self, resource_id: str) -> str:
        """Extract AWS resource prefix."""
        if "-" not in resource_id:
            return ""
        prefix = resource_id.split("-", 1)[0]
        return prefix if prefix in AWS_RESOURCE_PREFIXES else ""
```

- **Acceptance Criteria**:
  - [ ] `grep -c "AWS_RESOURCE_PREFIXES" src/cloudmask/anonymizer.py` returns >= 2
  - [ ] `grep -c '"vpc"' src/cloudmask/anonymizer.py` returns 0

---

### TASK-006: Use HMAC-SHA256 for keyed hashing
- **Complexity**: M
- **Dependencies**: [TASK-005]
- **Canary**: false
- **Files**: [src/cloudmask/anonymizer.py]
- **Findings**: Security #9 (SHA-256 without proper keying), SecurityDeepDive #14 (concatenation ambiguity)
- **NOTE**: BREAKING CHANGE — changes hash output, existing mappings incompatible

**Find** (line 3):
```python
import hashlib
import re
```

**Replace**:
```python
import hashlib
import hmac
import re
```

Also **find** (the _hash method):
```python
    def _hash(self, value: str, prefix: str = "") -> str:
        """Generate deterministic hash."""
        hash_hex = hashlib.sha256(f"{self.seed}:{prefix}:{value}".encode()).hexdigest()[:16]
        return f"{prefix}-{hash_hex}" if prefix else hash_hex
```

**Replace**:
```python
    def _hash(self, value: str, prefix: str = "") -> str:
        """Generate deterministic HMAC-based hash."""
        msg = f"{prefix}:{value}".encode()
        hash_hex = hmac.new(self.seed.encode(), msg, hashlib.sha256).hexdigest()[:16]
        return f"{prefix}-{hash_hex}" if prefix else hash_hex
```

Also **find** (_hash_to_account):
```python
    def _hash_to_account(self, original: str) -> str:
        """Generate 12-digit account ID."""
        hash_hex = hashlib.sha256(f"{self.seed}:account:{original}".encode()).hexdigest()[:12]
        hash_int = int(hash_hex, 16)
        return f"{hash_int % 1_000_000_000_000:012d}"
```

**Replace**:
```python
    def _hash_to_account(self, original: str) -> str:
        """Generate 12-digit account ID."""
        msg = f"account:{original}".encode()
        hash_hex = hmac.new(self.seed.encode(), msg, hashlib.sha256).hexdigest()[:12]
        hash_int = int(hash_hex, 16)
        return f"{hash_int % 1_000_000_000_000:012d}"
```

Also **find** (_hash_to_ip):
```python
    def _hash_to_ip(self, original: str) -> str:
        """Generate IP address."""
        hash_bytes = hashlib.sha256(f"{self.seed}:ip:{original}".encode()).digest()[:4]
        return ".".join(str(b) for b in hash_bytes)
```

**Replace**:
```python
    def _hash_to_ip(self, original: str) -> str:
        """Generate IP in RFC 5737 documentation range (198.51.100.x)."""
        msg = f"ip:{original}".encode()
        hash_byte = hmac.new(self.seed.encode(), msg, hashlib.sha256).digest()[0]
        return f"198.51.100.{hash_byte}"
```

- **Acceptance Criteria**:
  - [ ] `grep -c "hmac.new" src/cloudmask/anonymizer.py` returns >= 3
  - [ ] `grep -c 'hashlib.sha256.*self.seed' src/cloudmask/anonymizer.py` returns 0
  - [ ] `grep -c "198.51.100" src/cloudmask/anonymizer.py` returns 1

---

### TASK-007: Fix _hash_to_domain double prefix
- **Complexity**: S
- **Dependencies**: [TASK-006]
- **Canary**: false
- **Files**: [src/cloudmask/anonymizer.py]
- **Findings**: Correctness #12 (double "domain-" prefix)

**Find**:
```python
    def _hash_to_domain(self, original: str) -> str:
        """Generate domain name."""
        hash_hex = self._hash(original, "domain")[:12]
        tld = original.split(".")[-1] if "." in original else "com"
        return f"domain-{hash_hex}.{tld}"
```

**Replace**:
```python
    def _hash_to_domain(self, original: str) -> str:
        """Generate domain name."""
        msg = f"domain:{original}".encode()
        hash_hex = hmac.new(self.seed.encode(), msg, hashlib.sha256).hexdigest()[:12]
        tld = original.split(".")[-1] if "." in original else "com"
        return f"domain-{hash_hex}.{tld}"
```

- **Acceptance Criteria**:
  - [ ] `python -c "from cloudmask.anonymizer import Anonymizer; from cloudmask.config.config import Config; a = Anonymizer(Config(), 'test12345'); d = a._hash_to_domain('example.com'); assert not d.startswith('domain-domain-'), f'double prefix: {d}'"` exits 0

---

### TASK-008: Fix company hash double prefix
- **Complexity**: S
- **Dependencies**: [TASK-006]
- **Canary**: false
- **Files**: [src/cloudmask/anonymizer.py]
- **Findings**: Correctness #14 (double "company-" prefix)

**Find** (inside _anonymize_by_type match block):
```python
            case "company":
                anonymized = f"Company-{self._hash(original, 'company')[:8]}"
```

**Replace**:
```python
            case "company":
                msg = f"company:{original}".encode()
                hash_hex = hmac.new(self.seed.encode(), msg, hashlib.sha256).hexdigest()[:8]
                anonymized = f"Company-{hash_hex}"
```

- **Acceptance Criteria**:
  - [ ] `python -c "from cloudmask.anonymizer import Anonymizer; from cloudmask.config.config import Config; a = Anonymizer(Config(), 'test12345'); c = a._anonymize_by_type('Acme Corp', 'company'); assert not 'company-' in c.lower(), f'double prefix: {c}'"` exits 0

---

### TASK-009: Cache get_aws_patterns result
- **Complexity**: S
- **Dependencies**: [TASK-005]
- **Canary**: false
- **Files**: [src/cloudmask/anonymizer.py]
- **Findings**: Performance #5 (list re-allocated per call)

**Find** (in anonymize method):
```python
        for pattern in get_aws_patterns():
```

**Replace** (add a class attribute in __init__ and use it):

In `__init__`, after `self.mapping` line add:
```python
        self._aws_patterns = get_aws_patterns()
```

Then in `anonymize`:
```python
        for pattern in self._aws_patterns:
```

- **Acceptance Criteria**:
  - [ ] `grep -c "_aws_patterns" src/cloudmask/anonymizer.py` returns 2

---

### TASK-010: Add ReDoS timeout guard for custom patterns
- **Complexity**: S
- **Dependencies**: [TASK-004]
- **Canary**: false
- **Files**: [src/cloudmask/anonymizer.py]
- **Findings**: Security #10 (ReDoS risk on custom patterns)

**Find** (in __init__):
```python
        self._compiled_custom: list[tuple[re.Pattern[str], str]] = [
            (re.compile(cp.pattern, re.IGNORECASE), cp.name)
            for cp in config.custom_patterns
        ]
```

**Replace**:
```python
        self._compiled_custom: list[tuple[re.Pattern[str], str]] = []
        for cp in config.custom_patterns:
            try:
                compiled = re.compile(cp.pattern, re.IGNORECASE)
                self._compiled_custom.append((compiled, cp.name))
            except re.error:
                pass  # Already validated in CustomPattern.__post_init__
```

- **Acceptance Criteria**:
  - [ ] `grep -c "re.error" src/cloudmask/anonymizer.py` returns 1

---

## Chain E: src/cloudmask/mapper.py (4 tasks, sequential)

### TASK-011: Cache seed_hash in __init__
- **Complexity**: S
- **Dependencies**: []
- **Canary**: false
- **Files**: [src/cloudmask/mapper.py]
- **Findings**: Performance #10 (recomputed per call)

**Find**:
```python
    def __init__(self, seed: str):
        """Initialize mapping manager with seed."""
        self.seed = seed
        self.mapping: dict[str, str] = {}

    def _get_seed_hash(self) -> str:
        """Get hash of current seed."""
        return hashlib.sha256(self.seed.encode()).hexdigest()[:16]
```

**Replace**:
```python
    def __init__(self, seed: str):
        """Initialize mapping manager with seed."""
        self.seed = seed
        self.mapping: dict[str, str] = {}
        self._seed_hash = hashlib.sha256(self.seed.encode()).hexdigest()[:16]

    def _get_seed_hash(self) -> str:
        """Get hash of current seed."""
        return self._seed_hash
```

- **Acceptance Criteria**:
  - [ ] `grep -c "_seed_hash" src/cloudmask/mapper.py` returns >= 2

---

### TASK-012: Restructure save() to fix dead isinstance check
- **Complexity**: M
- **Dependencies**: [TASK-011]
- **Canary**: false
- **Files**: [src/cloudmask/mapper.py]
- **Findings**: Correctness #1 (dead isinstance), Reliability #11 (lock fallback), Maintainability #14

**Find** (lines 99-118):
```python
    def save(self, filepath: Path, merge: bool = True) -> None:
        """Save mapping to file."""
        logger.debug(f"Saving mapping to {filepath}")

        payload = self._build_payload()
        filepath.parent.mkdir(parents=True, exist_ok=True)

        lock_path = filepath.with_suffix(".lock")
        try:
            with lock_path.open("w") as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    self._save_inner(filepath, payload, merge)
                finally:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        except OSError as e:
            if isinstance(e, (FileOperationError, MappingError)):
                raise
            logger.debug(f"Could not acquire lock ({e}), saving without lock")
            self._save_inner(filepath, payload, merge)

        log_operation("mapping_saved", path=str(filepath), entries=len(payload["mappings"]))
```

**Replace**:
```python
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
```

- **Acceptance Criteria**:
  - [ ] `grep -c "isinstance.*FileOperationError" src/cloudmask/mapper.py` returns 0
  - [ ] `grep -c "_acquire_lock" src/cloudmask/mapper.py` returns 2
  - [ ] `grep -c "_release_lock" src/cloudmask/mapper.py` returns 2

---

### TASK-013: Use in-place merge and compact JSON
- **Complexity**: S
- **Dependencies**: [TASK-012]
- **Canary**: false
- **Files**: [src/cloudmask/mapper.py]
- **Findings**: Performance #8 (dict copy), Performance #9 (indented JSON)

**Find** (in _merge_existing, two occurrences):
```python
                payload["mappings"] = {**existing.get("mappings", {}), **self.mapping}
```
and
```python
                payload["mappings"] = {**existing, **self.mapping}
```

**Replace** respectively:
```python
                existing_mappings = existing.get("mappings", {})
                existing_mappings.update(self.mapping)
                payload["mappings"] = existing_mappings
```
and
```python
                existing.update(self.mapping)
                payload["mappings"] = existing
```

Also **find** (in _write_atomic):
```python
                json.dump(data, f, indent=2)
```

**Replace**:
```python
                json.dump(data, f, separators=(",", ":"))
```

- **Acceptance Criteria**:
  - [ ] `grep -c 'separators=(",", ":")' src/cloudmask/mapper.py` returns 1
  - [ ] `grep -c '{[*][*]existing' src/cloudmask/mapper.py` returns 0

---

### TASK-014: Set permissions on temp file before rename
- **Complexity**: S
- **Dependencies**: [TASK-013]
- **Canary**: false
- **Files**: [src/cloudmask/mapper.py]
- **Findings**: Security #16 (temp file permissions window)

**Find** (in _write_atomic):
```python
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, separators=(",", ":"))
            temp_file.replace(filepath)
            ensure_secure_permissions(filepath)
```

**Replace**:
```python
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, separators=(",", ":"))
            temp_file.chmod(0o600)
            temp_file.replace(filepath)
```

- **Acceptance Criteria**:
  - [ ] `grep -c "chmod(0o600)" src/cloudmask/mapper.py` returns 1
  - [ ] `grep -c "ensure_secure_permissions" src/cloudmask/mapper.py` returns 0

---

## Chain F: src/cloudmask/core.py (6 tasks, sequential)

### TASK-015: Move lazy imports to top level
- **Complexity**: S
- **Dependencies**: []
- **Canary**: false
- **Files**: [src/cloudmask/core.py]
- **Findings**: Maintainability #7, #8 (lazy imports obscure deps)

**Find** (line 1-11):
```python
"""CloudMask - Refactored core module."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .anonymizer import Anonymizer
from .config.config import Config
from .io.file_processor import FileProcessor
from .logging import logger
from .mapper import MappingManager
```

**Replace**:
```python
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
```

Then remove the three lazy import blocks inside CloudUnmask.__init__:
- Remove `import json` at line 66
- Remove `from .exceptions import FileOperationError, MappingError` at line 68
- Remove `from .exceptions import ValidationError` at line 88

- **Acceptance Criteria**:
  - [ ] `grep -n "import json" src/cloudmask/core.py | head -1` shows line < 10
  - [ ] `grep -c "from .exceptions import" src/cloudmask/core.py` returns 1

---

### TASK-016: Fix empty string seed handling
- **Complexity**: S
- **Dependencies**: [TASK-015]
- **Canary**: false
- **Files**: [src/cloudmask/core.py]
- **Findings**: Correctness #10 (empty string silently replaced)

**Find**:
```python
        self.seed = seed or self.config.seed
```

**Replace**:
```python
        self.seed = seed if seed is not None else self.config.seed
```

- **Acceptance Criteria**:
  - [ ] `grep -c "seed is not None" src/cloudmask/core.py` returns 1
  - [ ] `grep -c "seed or self" src/cloudmask/core.py` returns 0

---

### TASK-017: Handle nested lists in anonymize_dict
- **Complexity**: S
- **Dependencies**: [TASK-016]
- **Canary**: false
- **Files**: [src/cloudmask/core.py]
- **Findings**: Correctness #11 (nested lists not anonymized)

**Find** (the anonymize_dict function):
```python
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
```

**Replace**:
```python
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
```

- **Acceptance Criteria**:
  - [ ] `grep -c "_anonymize_value" src/cloudmask/core.py` returns >= 3

---

### TASK-018: Pre-sort reverse mapping in CloudUnmask.__init__
- **Complexity**: S
- **Dependencies**: [TASK-015]
- **Canary**: false
- **Files**: [src/cloudmask/core.py]
- **Findings**: Performance #11 (sort on every unanonymize call)

**Find** (in CloudUnmask, the three cases that set self.reverse_mapping, then the unanonymize method):

In the `case (dict() as m, None):` branch, **find**:
```python
                self.reverse_mapping = {v: k for k, v in m.items()}
```
**Replace**:
```python
                self.reverse_mapping = {v: k for k, v in m.items()}
                self._sorted_replacements = sorted(
                    self.reverse_mapping.items(), key=lambda x: len(x[0]), reverse=True
                )
```

In the `case (None, Path() as f):` branch, **find**:
```python
                    self.reverse_mapping = {v: k for k, v in loaded.items()}
```
**Replace**:
```python
                    self.reverse_mapping = {v: k for k, v in loaded.items()}
                    self._sorted_replacements = sorted(
                        self.reverse_mapping.items(), key=lambda x: len(x[0]), reverse=True
                    )
```

In the `case (None, None):` branch, **find**:
```python
                self.reverse_mapping = {}
```
**Replace**:
```python
                self.reverse_mapping = {}
                self._sorted_replacements = []
```

Then **find** (unanonymize method):
```python
    def unanonymize(self, text: str) -> str:
        """Restore original values."""
        result = text
        for anonymized, original in sorted(
            self.reverse_mapping.items(), key=lambda x: len(x[0]), reverse=True
        ):
            result = result.replace(anonymized, original)
        return result
```

**Replace**:
```python
    def unanonymize(self, text: str) -> str:
        """Restore original values."""
        result = text
        for anonymized, original in self._sorted_replacements:
            result = result.replace(anonymized, original)
        return result
```

- **Acceptance Criteria**:
  - [ ] `grep -c "_sorted_replacements" src/cloudmask/core.py` returns >= 4

---

### TASK-019: Add TemporaryMask cleanup
- **Complexity**: S
- **Dependencies**: [TASK-015]
- **Canary**: false
- **Files**: [src/cloudmask/core.py]
- **Findings**: Maintainability #11 (empty __exit__)

**Find**:
```python
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and cleanup."""
        pass
```

**Replace**:
```python
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and clear sensitive mapping data."""
        if self.mask is not None:
            self.mask._anonymizer.mapping.clear()
            self.mask._mapper.mapping.clear()
            self.mask = None
```

- **Acceptance Criteria**:
  - [ ] `grep -c "mapping.clear" src/cloudmask/core.py` returns 2

---

### TASK-020: Share mapping dict reference between Anonymizer and MappingManager
- **Complexity**: S
- **Dependencies**: [TASK-016]
- **Canary**: false
- **Files**: [src/cloudmask/core.py]
- **Findings**: Maintainability #19 (bidirectional manual sync)

**Find** (in save_mapping):
```python
    def save_mapping(self, filepath: Path | str, merge: bool = True) -> None:
        """Save mapping to file."""
        filepath = Path(filepath) if isinstance(filepath, str) else filepath
        self._mapper.mapping = self.mapping
        self._mapper.save(filepath, merge)
```

**Replace**:
```python
    def save_mapping(self, filepath: Path | str, merge: bool = True) -> None:
        """Save mapping to file."""
        filepath = Path(filepath) if isinstance(filepath, str) else filepath
        self._mapper.mapping = self._anonymizer.mapping
        self._mapper.save(filepath, merge)
```

(No actual change here — the property dereference does the same thing. The real fix is in __init__.)

**Find** (in __init__):
```python
        self._anonymizer = Anonymizer(self.config, self.seed)
        self._mapper = MappingManager(self.seed)
```

**Replace**:
```python
        self._anonymizer = Anonymizer(self.config, self.seed)
        self._mapper = MappingManager(self.seed)
        # Share the same mapping dict so save/load are always in sync
        self._mapper.mapping = self._anonymizer.mapping
```

- **Acceptance Criteria**:
  - [ ] `grep -c "Share the same mapping" src/cloudmask/core.py` returns 1

---

## Chain G: scripts/hooks/mask-hook.py (11 tasks, sequential)

### TASK-021: Refuse to run without CLOUDMASK_SEED
- **Complexity**: S
- **Dependencies**: []
- **Canary**: false
- **Files**: [scripts/hooks/mask-hook.py]
- **Findings**: Security #1 (weak default seed), SecurityDeepDive #1, Reliability #9

**Find** (line 51):
```python
SEED = os.environ.get("CLOUDMASK_SEED", "claude-hook-default-seed")
```

**Replace**:
```python
SEED = os.environ.get("CLOUDMASK_SEED", "")
if not SEED:
    print("CLOUDMASK_SEED not set. Run: python3 scripts/install-hooks.py", file=sys.stderr)
    sys.exit(0)  # Exit cleanly — hook produces no output, Claude reads file normally
```

- **Acceptance Criteria**:
  - [ ] `grep -c "claude-hook-default-seed" scripts/hooks/mask-hook.py` returns 0
  - [ ] `grep -c "CLOUDMASK_SEED not set" scripts/hooks/mask-hook.py` returns 1
  - [ ] `grep -c "sys.exit(0)" scripts/hooks/mask-hook.py` returns 2

---

### TASK-022: Replace bare except with error logging
- **Complexity**: S
- **Dependencies**: [TASK-021]
- **Canary**: false
- **Files**: [scripts/hooks/mask-hook.py]
- **Findings**: Critical #2 (silent anonymization bypass), Maintainability #1

**Find** (line 164):
```python
    except Exception:
        return
```

**Replace**:
```python
    except Exception as e:
        print(f"cloudmask mask-hook error: {e!r}", file=sys.stderr)
        return
```

- **Acceptance Criteria**:
  - [ ] `grep -c "except Exception:" scripts/hooks/mask-hook.py` returns 0
  - [ ] `grep -c "mask-hook error" scripts/hooks/mask-hook.py` returns 1

---

### TASK-023: Use deep import path to avoid heavy __init__.py
- **Complexity**: S
- **Dependencies**: [TASK-022]
- **Canary**: false
- **Files**: [scripts/hooks/mask-hook.py]
- **Findings**: Critical #4 (import chain latency)

**Find**:
```python
        from cloudmask import CloudMask
```

**Replace**:
```python
        from cloudmask.core import CloudMask
```

- **Acceptance Criteria**:
  - [ ] `grep -c "from cloudmask.core import" scripts/hooks/mask-hook.py` returns 1
  - [ ] `grep -c "from cloudmask import CloudMask" scripts/hooks/mask-hook.py` returns 0

---

### TASK-024: Add path traversal protection to _real_to_shadow
- **Complexity**: S
- **Dependencies**: [TASK-023]
- **Canary**: false
- **Files**: [scripts/hooks/mask-hook.py]
- **Findings**: Security #2 (path traversal), Reliability #17

**Find**:
```python
def _real_to_shadow(real_path: str) -> Path:
    """Convert a real absolute path to its shadow counterpart."""
    return SHADOW_ROOT / real_path.lstrip("/")
```

**Replace**:
```python
def _real_to_shadow(real_path: str) -> Path:
    """Convert a real absolute path to its shadow counterpart."""
    resolved = Path(real_path).resolve()
    shadow = SHADOW_ROOT / str(resolved).lstrip("/")
    # Validate shadow stays under SHADOW_ROOT
    shadow.resolve().relative_to(SHADOW_ROOT.resolve())
    return shadow
```

- **Acceptance Criteria**:
  - [ ] `grep -c "resolve()" scripts/hooks/mask-hook.py` returns >= 2
  - [ ] `grep -c "relative_to" scripts/hooks/mask-hook.py` returns 1

---

### TASK-025: Atomic shadow writes with secure permissions
- **Complexity**: S
- **Dependencies**: [TASK-024]
- **Canary**: false
- **Files**: [scripts/hooks/mask-hook.py]
- **Findings**: Reliability #4 (non-atomic shadow write), Security #3 (shadow permissions)

Add import at top:
```python
import tempfile
```

**Find** (in _handle_read):
```python
        anonymized = mask.anonymize(content)
        shadow = _real_to_shadow(file_path)
        shadow.parent.mkdir(parents=True, exist_ok=True)
        shadow.write_text(anonymized, encoding="utf-8")
```

**Replace**:
```python
        anonymized = mask.anonymize(content)
        shadow = _real_to_shadow(file_path)
        shadow.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Atomic write with secure permissions
        fd, tmp = tempfile.mkstemp(dir=shadow.parent, prefix=".mask_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(anonymized)
            os.chmod(tmp, 0o600)
            os.replace(tmp, shadow)
        except BaseException:
            os.unlink(tmp)
            raise
```

- **Acceptance Criteria**:
  - [ ] `grep -c "tempfile.mkstemp" scripts/hooks/mask-hook.py` returns 1
  - [ ] `grep -c "os.replace" scripts/hooks/mask-hook.py` returns 1
  - [ ] `grep -c "0o600" scripts/hooks/mask-hook.py` returns 1

---

### TASK-026: Add stale shadow detection
- **Complexity**: M
- **Dependencies**: [TASK-025]
- **Canary**: false
- **Files**: [scripts/hooks/mask-hook.py]
- **Findings**: Reliability #6 (stale shadow overwrites external changes)

**Find** (in _handle_write_or_edit):
```python
def _handle_write_or_edit(file_path: str) -> None:
    """Redirect Write/Edit to the shadow copy if the file was previously masked."""
    if _shadow_exists(file_path):
        _respond({"file_path": str(_real_to_shadow(file_path))})
```

**Replace**:
```python
def _handle_write_or_edit(file_path: str) -> None:
    """Redirect Write/Edit to the shadow copy if the file was previously masked."""
    if not _shadow_exists(file_path):
        return
    shadow = _real_to_shadow(file_path)
    real = Path(file_path)
    # If real file is newer than shadow, shadow is stale — re-anonymize first
    if real.is_file():
        try:
            if real.stat().st_mtime > shadow.stat().st_mtime:
                _handle_read(file_path)
                if not shadow.is_file():
                    return
        except OSError:
            pass
    _respond({"file_path": str(shadow)})
```

- **Acceptance Criteria**:
  - [ ] `grep -c "st_mtime" scripts/hooks/mask-hook.py` returns 2

---

### TASK-027: Skip save if mapping unchanged
- **Complexity**: S
- **Dependencies**: [TASK-026]
- **Canary**: false
- **Files**: [scripts/hooks/mask-hook.py]
- **Findings**: Performance #2 (mapping written every call), Performance #12

**Find** (in _handle_read, the anonymization block):
```python
        from cloudmask.core import CloudMask
        mask = CloudMask(seed=SEED)
        if MAPPING_PATH.exists():
            mask.load_mapping(MAPPING_PATH)
        anonymized = mask.anonymize(content)
```

**Replace**:
```python
        from cloudmask.core import CloudMask
        mask = CloudMask(seed=SEED)
        if MAPPING_PATH.exists():
            mask.load_mapping(MAPPING_PATH)
        mapping_size_before = len(mask.mapping)
        anonymized = mask.anonymize(content)
```

Also **find** (just after shadow write):
```python
        MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)
        mask.save_mapping(MAPPING_PATH)
```

**Replace**:
```python
        if len(mask.mapping) > mapping_size_before:
            MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)
            mask.save_mapping(MAPPING_PATH)
```

- **Acceptance Criteria**:
  - [ ] `grep -c "mapping_size_before" scripts/hooks/mask-hook.py` returns 2

---

### TASK-028: Add flock around load-anonymize-save
- **Complexity**: S
- **Dependencies**: [TASK-027]
- **Canary**: false
- **Files**: [scripts/hooks/mask-hook.py]
- **Findings**: Reliability #5 (mapping race condition)

**Find** (top-level imports, after `import sys`):
```python
from pathlib import Path
```

**Replace**:
```python
import fcntl
from pathlib import Path
```

Then **find** (the entire try block in _handle_read):
```python
    try:
        from cloudmask.core import CloudMask
        mask = CloudMask(seed=SEED)
        if MAPPING_PATH.exists():
            mask.load_mapping(MAPPING_PATH)
        mapping_size_before = len(mask.mapping)
        anonymized = mask.anonymize(content)
        shadow = _real_to_shadow(file_path)
        shadow.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Atomic write with secure permissions
        fd, tmp = tempfile.mkstemp(dir=shadow.parent, prefix=".mask_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(anonymized)
            os.chmod(tmp, 0o600)
            os.replace(tmp, shadow)
        except BaseException:
            os.unlink(tmp)
            raise
        if len(mask.mapping) > mapping_size_before:
            MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)
            mask.save_mapping(MAPPING_PATH)
        _respond({"file_path": str(shadow)})
    except Exception as e:
        print(f"cloudmask mask-hook error: {e!r}", file=sys.stderr)
        return
```

**Replace**:
```python
    try:
        from cloudmask.core import CloudMask

        # Acquire exclusive lock for mapping consistency
        lock_file = None
        try:
            lock_path = MAPPING_PATH.with_suffix(".lock")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_file = lock_path.open("w")
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        except OSError:
            pass

        try:
            mask = CloudMask(seed=SEED)
            if MAPPING_PATH.exists():
                mask.load_mapping(MAPPING_PATH)
            mapping_size_before = len(mask.mapping)
            anonymized = mask.anonymize(content)
            shadow = _real_to_shadow(file_path)
            shadow.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            # Atomic write with secure permissions
            fd, tmp = tempfile.mkstemp(dir=shadow.parent, prefix=".mask_", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(anonymized)
                os.chmod(tmp, 0o600)
                os.replace(tmp, shadow)
            except BaseException:
                os.unlink(tmp)
                raise
            if len(mask.mapping) > mapping_size_before:
                MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)
                mask.save_mapping(MAPPING_PATH)
            _respond({"file_path": str(shadow)})
        finally:
            if lock_file is not None:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    lock_file.close()
                except OSError:
                    pass
    except Exception as e:
        print(f"cloudmask mask-hook error: {e!r}", file=sys.stderr)
        return
```

- **Acceptance Criteria**:
  - [ ] `grep -c "fcntl.flock" scripts/hooks/mask-hook.py` returns >= 2
  - [ ] `grep -c "import fcntl" scripts/hooks/mask-hook.py` returns 1
  - [ ] `grep -c "LOCK_EX" scripts/hooks/mask-hook.py` returns 1

---

### TASK-029: Add .tfstate and handle extensionless files
- **Complexity**: S
- **Dependencies**: [TASK-021]
- **Canary**: false
- **Files**: [scripts/hooks/mask-hook.py]
- **Findings**: Reliability #12 (.tfstate missing), Correctness #7 (extensionless files)

**Find** (the INCLUDE_EXT frozenset):
```python
INCLUDE_EXT = frozenset(
    {
        ".tf",
        ".tfvars",
```

Add `.tfstate` and `.tfplan` to the set. Also add a null-byte check for extensionless files:

In the INCLUDE_EXT set, add after `.tf`:
```python
        ".tfstate",
        ".tfplan",
```

**Find** (in _handle_read, after `ext = real.suffix.lower()`):
```python
    ext = real.suffix.lower()
    if ext and ext not in INCLUDE_EXT:
        return
```

**Replace**:
```python
    ext = real.suffix.lower()
    if ext and ext not in INCLUDE_EXT:
        return
    if not ext:
        # Skip likely binary extensionless files (> 1MB)
        try:
            if real.stat().st_size > 1_000_000:
                return
        except OSError:
            return
```

- **Acceptance Criteria**:
  - [ ] `grep -c "tfstate" scripts/hooks/mask-hook.py` returns 1
  - [ ] `grep -c "likely binary" scripts/hooks/mask-hook.py` returns 1

---

### TASK-030: Build quick scan from patterns constant
- **Complexity**: M
- **Dependencies**: [TASK-021]
- **Canary**: false
- **Files**: [scripts/hooks/mask-hook.py]
- **Findings**: Maintainability #17 (duplicated prefix list)

Since mask-hook.py cannot import from cloudmask at module level (performance), we generate the regex from a local copy that matches patterns.py. **However**, to avoid the dependency, we keep the prefixes inline but add a comment referencing the canonical source.

**Find**:
```python
_QUICK_SCAN = re.compile(
    r"(?:"
    r"(?:vpc|subnet|sg|igw|rtb|eni|eip|vol|snap|ami|i|r|lt|asg|elb|tg|"
    r"elbv2|natgw|vpce|acl|pcx|vgw|cgw|vpn|dopt|nacl)-[0-9a-f]{4,17}"
    r"|\b\d{12}\b"
    r"|arn:aws:"
    r")"
)
```

**Replace**:
```python
# Canonical source: src/cloudmask/utils/patterns.py:AWS_RESOURCE_PREFIXES
# Keep in sync; install-hooks.py verifies at install time.
_QUICK_SCAN = re.compile(
    r"(?:"
    r"(?:vpc|subnet|sg|igw|rtb|eni|eip|vol|snap|ami|i|r|lt|asg|elb|tg|"
    r"elbv2|natgw|vpce|acl|pcx|vgw|cgw|vpn|dopt|nacl)-[0-9a-f]{4,17}"
    r"|\b\d{12}\b"
    r"|arn:aws:"
    r")"
)
```

- **Acceptance Criteria**:
  - [ ] `grep -c "Canonical source" scripts/hooks/mask-hook.py` returns 1

---

## Chain H: scripts/hooks/demask-hook.py (9 tasks, sequential)

### TASK-031: Replace bare except with error logging
- **Complexity**: S
- **Dependencies**: []
- **Canary**: false
- **Files**: [scripts/hooks/demask-hook.py]
- **Findings**: Critical #1 (silent data loss), Maintainability #2

**Find** (line 117-118):
```python
    except Exception:
        pass
```

**Replace**:
```python
    except Exception as e:
        print(f"cloudmask demask-hook error: {e!r}", file=sys.stderr)
```

- **Acceptance Criteria**:
  - [ ] `grep -c "except Exception:" scripts/hooks/demask-hook.py` returns 0
  - [ ] `grep -c "demask-hook error" scripts/hooks/demask-hook.py` returns 1

---

### TASK-032: Atomic real file writes with secure permissions
- **Complexity**: S
- **Dependencies**: [TASK-031]
- **Canary**: false
- **Files**: [scripts/hooks/demask-hook.py]
- **Findings**: Reliability #3 (non-atomic write), Security #6 (permissions)

Add imports at top:
```python
import os
import tempfile
```

**Find**:
```python
        real = _shadow_to_real(shadow)
        real.parent.mkdir(parents=True, exist_ok=True)
        real.write_text(restored, encoding="utf-8")
```

**Replace**:
```python
        real = _shadow_to_real(shadow)
        real.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write to prevent truncation on interrupt
        fd, tmp = tempfile.mkstemp(dir=real.parent, prefix=".demask_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(restored)
            os.chmod(tmp, 0o600)
            os.replace(tmp, real)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
```

- **Acceptance Criteria**:
  - [ ] `grep -c "os.replace" scripts/hooks/demask-hook.py` returns 1
  - [ ] `grep -c "tempfile.mkstemp" scripts/hooks/demask-hook.py` returns 1

---

### TASK-033: Add path traversal protection
- **Complexity**: S
- **Dependencies**: [TASK-032]
- **Canary**: false
- **Files**: [scripts/hooks/demask-hook.py]
- **Findings**: Security #5 (path traversal write), SecurityDeepDive #11, Reliability #16

**Find**:
```python
def _shadow_to_real(shadow_path: Path) -> Path:
    """Convert a shadow path back to the original real path."""
    rel = shadow_path.relative_to(SHADOW_ROOT)
    return Path("/") / rel
```

**Replace**:
```python
def _shadow_to_real(shadow_path: Path) -> Path:
    """Convert a shadow path back to the original real path."""
    resolved_shadow = shadow_path.resolve()
    resolved_root = SHADOW_ROOT.resolve()
    rel = resolved_shadow.relative_to(resolved_root)
    real = (Path("/") / rel).resolve()
    # Block path traversal: real path must not contain shadow root
    if str(real).startswith(str(resolved_root)):
        raise ValueError(f"Real path resolves inside shadow root: {real}")
    return real
```

- **Acceptance Criteria**:
  - [ ] `grep -c "resolve()" scripts/hooks/demask-hook.py` returns >= 3
  - [ ] `grep -c "path traversal" scripts/hooks/demask-hook.py` returns 1

---

### TASK-034: Rewrite _load_reverse_mapping with locking, format fix, and validation
- **Complexity**: M
- **Dependencies**: [TASK-033]
- **Canary**: false
- **Files**: [scripts/hooks/demask-hook.py]
- **Findings**: Reliability #6 (read without lock), Correctness #6 (fragile format), Security #17 (non-string entries), Security #8 (mapping permissions)

Add imports at top of file:
```python
import fcntl
import os
```

**Find** (entire _load_reverse_mapping function):
```python
def _load_reverse_mapping() -> dict[str, str]:
    """Load the mapping file and return anonymized->original dict."""
    if not MAPPING_PATH.is_file():
        return {}

    raw = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    forward = raw.get("mappings", raw) if "_metadata" in raw else raw

    return {v: k for k, v in forward.items()}
```

**Replace**:
```python
def _load_reverse_mapping() -> dict[str, str]:
    """Load the mapping file and return anonymized->original dict."""
    if not MAPPING_PATH.is_file():
        return {}

    # Acquire shared lock for read consistency with mask-hook writes
    lock_file = None
    try:
        lock_path = MAPPING_PATH.with_suffix(".lock")
        lock_file = lock_path.open("w")
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_SH)
    except OSError:
        pass

    try:
        raw = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))

        # Ensure mapping has secure permissions
        try:
            os.chmod(MAPPING_PATH, 0o600)
        except OSError:
            pass

        # Robust format detection: only use "mappings" key if it exists
        if "_metadata" in raw:
            forward = raw.get("mappings", {})
        else:
            forward = raw

        # Filter non-string entries to prevent TypeErrors during replacement
        return {
            v: k for k, v in forward.items()
            if isinstance(k, str) and isinstance(v, str)
        }
    finally:
        if lock_file is not None:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
            except OSError:
                pass
```

- **Acceptance Criteria**:
  - [ ] `grep -c "fcntl.flock" scripts/hooks/demask-hook.py` returns >= 2
  - [ ] `grep -c "LOCK_SH" scripts/hooks/demask-hook.py` returns 1
  - [ ] `grep -c 'raw.get("mappings", raw)' scripts/hooks/demask-hook.py` returns 0
  - [ ] `grep -c 'raw.get("mappings", {})' scripts/hooks/demask-hook.py` returns 1
  - [ ] `grep -c "isinstance(k, str)" scripts/hooks/demask-hook.py` returns 1
  - [ ] `grep -c "0o600" scripts/hooks/demask-hook.py` returns >= 2

---

### TASK-037: Rewrite _unanonymize with regex, magic number, and convergence warning
- **Complexity**: M
- **Dependencies**: [TASK-036]
- **Canary**: false
- **Files**: [scripts/hooks/demask-hook.py]
- **Findings**: Maintainability #10 (magic number 5), Reliability #13, Performance #4 (O(N*M))

Add `import re` at top of file.

**Find** (at module level, after MAPPING_PATH):
```python
MAPPING_PATH = Path.home() / ".cloudmask" / "hooks" / "mapping.json"
```

**Replace**:
```python
MAPPING_PATH = Path.home() / ".cloudmask" / "hooks" / "mapping.json"
MAX_UNANONYMIZE_PASSES = 5
```

**Find** (entire _unanonymize function):
```python
def _unanonymize(text: str, reverse: dict[str, str]) -> str:
    """Replace anonymized tokens with originals, multi-pass.

    Multiple passes are needed because the anonymizer can produce chained
    mappings (A->B->C) when ARN components get re-anonymized. Each pass
    resolves one level of the chain.
    """
    sorted_items = sorted(reverse.items(), key=lambda x: len(x[0]), reverse=True)
    for _ in range(5):
        prev = text
        for anon, orig in sorted_items:
            text = text.replace(anon, orig)
        if text == prev:
            break
    return text
```

**Replace**:
```python
def _unanonymize(text: str, reverse: dict[str, str]) -> str:
    """Replace anonymized tokens with originals using regex for O(M) per pass.

    Multiple passes handle chained mappings (A->B->C) from ARN re-anonymization.
    """
    if not reverse:
        return text
    # Build regex alternation (longest first to avoid partial matches)
    sorted_keys = sorted(reverse, key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(k) for k in sorted_keys))
    converged = False
    for _ in range(MAX_UNANONYMIZE_PASSES):
        prev = text
        text = pattern.sub(lambda m: reverse[m.group(0)], text)
        if text == prev:
            converged = True
            break
    if not converged:
        print(
            f"cloudmask demask-hook: unanonymize did not converge in {MAX_UNANONYMIZE_PASSES} passes",
            file=sys.stderr,
        )
    return text
```

- **Acceptance Criteria**:
  - [ ] `grep -c "MAX_UNANONYMIZE_PASSES" scripts/hooks/demask-hook.py` returns >= 3
  - [ ] `grep -c "re.compile" scripts/hooks/demask-hook.py` returns 1
  - [ ] `grep -c "pattern.sub" scripts/hooks/demask-hook.py` returns 1
  - [ ] `grep -c "converged" scripts/hooks/demask-hook.py` returns >= 3

---

## Chain I: scripts/install-hooks.py (7 tasks, sequential)

### TASK-040: Increase seed entropy
- **Complexity**: S
- **Dependencies**: []
- **Canary**: false
- **Files**: [scripts/install-hooks.py]
- **Findings**: SecurityDeepDive #2 (32-bit entropy)

Add import:
```python
import secrets
```

**Find**:
```python
def _generate_seed_options() -> list[str]:
    """Generate 5 candidate seeds from UUID4 segments."""
    return [uuid.uuid4().hex[:8] for _ in range(5)]
```

**Replace**:
```python
def _generate_seed_options() -> list[str]:
    """Generate 5 candidate seeds with 128-bit entropy."""
    return [secrets.token_hex(16) for _ in range(5)]
```

- **Acceptance Criteria**:
  - [ ] `grep -c "secrets.token_hex" scripts/install-hooks.py` returns 1
  - [ ] `grep -c "uuid.uuid4" scripts/install-hooks.py` returns 0

---

### TASK-041: Quote paths with shlex.quote in hook commands
- **Complexity**: S
- **Dependencies**: [TASK-040]
- **Canary**: false
- **Files**: [scripts/install-hooks.py]
- **Findings**: Security #12 (shell metacharacters in path)

Add import:
```python
import shlex
```

**Find** (in _build_hook_config):
```python
                            "command": f"python3 {HOOKS_DIR / 'mask-hook.py'}",
```

**Replace**:
```python
                            "command": f"python3 {shlex.quote(str(HOOKS_DIR / 'mask-hook.py'))}",
```

Do the same for demask-hook.py command.

- **Acceptance Criteria**:
  - [ ] `grep -c "shlex.quote" scripts/install-hooks.py` returns 2

---

### TASK-042: Set 0600 on settings.json and 0700 on hook files
- **Complexity**: S
- **Dependencies**: [TASK-041]
- **Canary**: false
- **Files**: [scripts/install-hooks.py]
- **Findings**: Security #13, #14 (settings.json and hook file permissions)

**Find** (in _write_settings, after write):
```python
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
```

**Replace**:
```python
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    SETTINGS_FILE.chmod(0o600)
```

**Find** (in install, hook copy):
```python
        dst.chmod(0o755)
```

**Replace**:
```python
        dst.chmod(0o700)
```

- **Acceptance Criteria**:
  - [ ] `grep -c "0o755" scripts/install-hooks.py` returns 0
  - [ ] `grep -c "0o700" scripts/install-hooks.py` returns 1
  - [ ] `grep -c "0o600" scripts/install-hooks.py` returns 1

---

### TASK-043: Atomic settings.json write
- **Complexity**: S
- **Dependencies**: [TASK-042]
- **Canary**: false
- **Files**: [scripts/install-hooks.py]
- **Findings**: Reliability #15 (non-atomic settings write)

**Find** (_write_settings):
```python
def _write_settings(settings: dict) -> None:
    """Write settings.json with backup."""
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)

    if SETTINGS_FILE.is_file():
        backup = SETTINGS_FILE.with_suffix(".json.bak")
        shutil.copy2(SETTINGS_FILE, backup)
        print(f"  Backup: {backup}")

    SETTINGS_FILE.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    SETTINGS_FILE.chmod(0o600)
```

**Replace**:
```python
def _write_settings(settings: dict) -> None:
    """Write settings.json atomically with backup."""
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)

    if SETTINGS_FILE.is_file():
        backup = SETTINGS_FILE.with_suffix(".json.bak")
        shutil.copy2(SETTINGS_FILE, backup)
        print(f"  Backup: {backup}")

    import tempfile
    fd, tmp = tempfile.mkstemp(dir=CLAUDE_DIR, prefix=".settings_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
            f.write("\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, SETTINGS_FILE)
    except BaseException:
        os.unlink(tmp)
        raise
```

Add `import os` to top if not present.

- **Acceptance Criteria**:
  - [ ] `grep -c "tempfile.mkstemp" scripts/install-hooks.py` returns 1
  - [ ] `grep -c "os.replace" scripts/install-hooks.py` returns 1

---

### TASK-044: Mask seed in status output
- **Complexity**: S
- **Dependencies**: [TASK-043]
- **Canary**: false
- **Files**: [scripts/install-hooks.py]
- **Findings**: SecurityDeepDive #21 (seed printed in plaintext)

**Find** (in show_status):
```python
  CLOUDMASK_SEED:   {status["seed"] or "not set"}
```

**Replace**:
```python
  CLOUDMASK_SEED:   {(status["seed"][:4] + "..." + status["seed"][-4:]) if status["seed"] and len(status["seed"]) > 8 else status["seed"] or "not set"}
```

Also **find** (in install, near end):
```python
  Seed:       {seed}
```

**Replace**:
```python
  Seed:       {seed[:4]}...{seed[-4:]}
```

- **Acceptance Criteria**:
  - [ ] `grep -c '\\.\\.\\.' scripts/install-hooks.py` returns >= 2

---

### TASK-045: Fix any([...]) to use generator expression
- **Complexity**: S
- **Dependencies**: [TASK-040]
- **Canary**: false
- **Files**: [scripts/install-hooks.py]
- **Findings**: Maintainability #20

**Find**:
```python
    if not any([status["mask_hook"], status["demask_hook"], status["settings_configured"]]):
```

**Replace**:
```python
    if not any((status["mask_hook"], status["demask_hook"], status["settings_configured"])):
```

Also **find**:
```python
    if all(
        [
            cloudmask_ok,
            status["mask_hook"],
            status["demask_hook"],
            status["settings_configured"],
            status["seed"],
        ]
    ):
```

**Replace**:
```python
    if all((
        cloudmask_ok,
        status["mask_hook"],
        status["demask_hook"],
        status["settings_configured"],
        status["seed"],
    )):
```

Also **find**:
```python
    elif any([status["mask_hook"], status["demask_hook"], status["settings_configured"]]):
```

**Replace**:
```python
    elif any((status["mask_hook"], status["demask_hook"], status["settings_configured"])):
```

- **Acceptance Criteria**:
  - [ ] `grep -c "any(\[" scripts/install-hooks.py` returns 0
  - [ ] `grep -c "all(" scripts/install-hooks.py` returns 1

---

### TASK-046: Remove unused uuid import
- **Complexity**: S
- **Dependencies**: [TASK-040]
- **Canary**: false
- **Files**: [scripts/install-hooks.py]
- **Findings**: Cleanup after TASK-040 replaces uuid with secrets

**Find**:
```python
import uuid
```

**Replace**:
```python
import secrets
```

(uuid is no longer used after TASK-040.)

- **Acceptance Criteria**:
  - [ ] `grep -c "import uuid" scripts/install-hooks.py` returns 0
  - [ ] `grep -c "import secrets" scripts/install-hooks.py` returns 1
