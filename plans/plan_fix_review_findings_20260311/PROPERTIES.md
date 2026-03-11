---
title: Formal Properties for Review Findings Fix
created: 2026-03-11T11:00:00Z
---

# PROPERTIES: CloudMask Hooks System

## SAFETY Properties (must never happen)

### PROP-001: No Silent Data Loss
- **Type**: SAFETY
- **Priority**: critical
- **Statement**: The demask-hook must NEVER silently discard Claude's edits. If write-back to the real file fails, the error MUST be reported to stderr.
- **Rationale**: Critical #1 — bare `except: pass` causes silent data loss
- **Observable**: `grep -c "demask-hook error" scripts/hooks/demask-hook.py` returns >= 1
- **Tasks**: TASK-031

### PROP-002: No Silent Security Bypass
- **Type**: SAFETY
- **Priority**: critical
- **Statement**: The mask-hook must NEVER silently fall through to unmasked content without logging. If anonymization fails, the failure MUST be reported.
- **Rationale**: Critical #2 — bare `except: return` silently exposes secrets
- **Observable**: `grep -c "mask-hook error" scripts/hooks/mask-hook.py` returns >= 1
- **Tasks**: TASK-022

### PROP-003: No Path Traversal Writes
- **Type**: SAFETY
- **Priority**: high
- **Statement**: Shadow-to-real path derivation must NEVER produce a path outside the intended filesystem tree. All paths must be resolved and validated.
- **Rationale**: Security finding — symlinks in shadow dir could cause arbitrary writes
- **Observable**: `grep -c "resolve()" scripts/hooks/demask-hook.py` returns >= 3
- **Tasks**: TASK-024, TASK-033

### PROP-004: No Default Seed in Production
- **Type**: SAFETY
- **Priority**: high
- **Statement**: Hooks must NEVER anonymize with a publicly known default seed. If CLOUDMASK_SEED is not set, the hook must refuse to operate.
- **Rationale**: Default seed makes anonymization trivially reversible
- **Observable**: `grep -c "claude-hook-default-seed" scripts/hooks/mask-hook.py` returns 0
- **Tasks**: TASK-021

## LIVENESS Properties (must eventually happen)

### PROP-005: Atomic File Updates
- **Type**: LIVENESS
- **Priority**: high
- **Statement**: Every file write (shadow, real, mapping, settings) must eventually produce either a complete valid file or no change. Partial writes must never persist.
- **Rationale**: Reliability findings — non-atomic writes cause truncation on interrupt
- **Observable**: `grep -c "os.replace" scripts/hooks/demask-hook.py` returns 1 AND `grep -c "os.replace" scripts/hooks/mask-hook.py` returns 1
- **Tasks**: TASK-025, TASK-032, TASK-043

### PROP-006: Stale Shadow Detection
- **Type**: LIVENESS
- **Priority**: high
- **Statement**: When a Write/Edit redirects to a shadow file, the shadow must reflect the current state of the real file. Stale shadows must be refreshed before redirection.
- **Rationale**: Reliability finding — stale shadows silently destroy external changes
- **Observable**: `grep -c "st_mtime" scripts/hooks/mask-hook.py` returns >= 2
- **Tasks**: TASK-026

## INVARIANT Properties (must always be true)

### PROP-007: Mapping File Consistency
- **Type**: INVARIANT
- **Priority**: high
- **Statement**: The mapping file must always be a valid JSON object. Concurrent hook invocations must not corrupt it. File locking must be used for both reads and writes.
- **Rationale**: Race condition findings — concurrent hooks corrupt mapping
- **Observable**: `grep -c "fcntl.flock" scripts/hooks/mask-hook.py` returns >= 2 AND `grep -c "LOCK_SH" scripts/hooks/demask-hook.py` returns 1
- **Tasks**: TASK-028, TASK-034

### PROP-008: Secure File Permissions
- **Type**: INVARIANT
- **Priority**: high
- **Statement**: All sensitive files (mapping.json, shadow files, settings.json, hook files) must have owner-only permissions (0600 for files, 0700 for directories).
- **Rationale**: Multiple security findings about world-readable sensitive files
- **Observable**: `grep -c "0o600" scripts/hooks/demask-hook.py` returns >= 2 AND `grep -c "0o700" scripts/hooks/mask-hook.py` returns >= 1
- **Tasks**: TASK-025, TASK-032, TASK-039, TASK-042

### PROP-009: Single Source of Truth for Prefixes
- **Type**: INVARIANT
- **Priority**: medium
- **Statement**: The AWS resource prefix list must be defined exactly once in `patterns.py:AWS_RESOURCE_PREFIXES` and referenced (not duplicated) by all consumers.
- **Rationale**: Maintainability — prefix list duplicated in 3 locations
- **Observable**: `grep -c '"vpc"' src/cloudmask/anonymizer.py` returns 0
- **Tasks**: TASK-001, TASK-005

### PROP-010: HMAC-Based Keyed Hashing
- **Type**: INVARIANT
- **Priority**: medium
- **Statement**: All anonymization hashing must use HMAC-SHA256 with the seed as key, not plain SHA-256 with string concatenation.
- **Rationale**: Security — concatenation scheme has prefix collision vulnerability
- **Observable**: `grep -c "hmac.new" src/cloudmask/anonymizer.py` returns >= 3
- **Tasks**: TASK-006
- **NOTE**: Breaking change — requires mapping version bump

## PERFORMANCE Properties (time/resource bounds)

### PROP-011: Hook Import Under 50ms
- **Type**: PERFORMANCE
- **Priority**: critical
- **Statement**: `from cloudmask.core import CloudMask` must complete in under 50ms. The `__init__.py` must not eagerly import cryptography, yaml, streaming, ratelimit, or security modules.
- **Rationale**: Critical #4 — 130-380ms import overhead per tool call
- **Observable**: `grep -c "from .utils.security" src/cloudmask/__init__.py` returns 0 AND `grep -c "__getattr__" src/cloudmask/__init__.py` returns 1
- **Tasks**: TASK-002, TASK-023

### PROP-012: Mapping Save Only When Changed
- **Type**: PERFORMANCE
- **Priority**: high
- **Statement**: The mask-hook must skip `save_mapping()` when no new entries were added during anonymization. Unchanged mappings must not trigger I/O.
- **Rationale**: Performance finding — mapping read/written hundreds of times per session
- **Observable**: `grep -c "mapping_size_before" scripts/hooks/mask-hook.py` returns 2
- **Tasks**: TASK-027

### PROP-013: Seed Entropy >= 128 bits
- **Type**: PERFORMANCE
- **Priority**: high
- **Statement**: Auto-generated seeds must have at least 128 bits of entropy (32 hex characters).
- **Rationale**: SecurityDeepDive — 32-bit seeds brute-forceable in minutes
- **Observable**: `grep -c "secrets.token_hex(16)" scripts/install-hooks.py` returns 1
- **Tasks**: TASK-040
