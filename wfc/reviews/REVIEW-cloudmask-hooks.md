# Review Report: CloudMask Hooks + Core Engine

**Status**: BLOCKED
**Consensus Score**: CS=8.50 (Deep tier, minority protection triggered)
**Reviewers Spawned**: 6 (Security, Correctness, Performance, Maintainability, Reliability, SecurityDeepDive)
**Total Raw Findings**: 106
**Unique Findings After Dedup**: ~55
**Review Tier**: Deep (1,233 lines, security-sensitive code)

---

## Critical Findings (Severity 9-10)

### [CRITICAL] scripts/hooks/demask-hook.py:117
**Category**: reliability
**R_i**: 10.00 | **Reviewers**: Reliability(10), Maintainability(8), Security(6), SecurityDeepDive(6) (k=4 cross-category)

**Description**: Bare `except Exception: pass` silently swallows ALL errors during demasking and write-back. If reverse mapping fails, disk is full, or file write errors, Claude's edits are trapped in the shadow file and never reach the real file. **Silent data loss with zero user notification.**

**Remediation**: Log exceptions to stderr. Return non-zero exit code on failure. Use atomic writes (tempfile + rename) for the real file write. Never use bare `except: pass` on a data-critical write path.

---

### [CRITICAL] scripts/hooks/mask-hook.py:164
**Category**: reliability
**R_i**: 9.00 | **Reviewers**: Reliability(9), Maintainability(8), Security(5), SecurityDeepDive(4) (k=4 cross-category)

**Description**: Bare `except Exception: return` during anonymization causes Claude to silently read the REAL unmasked file when any error occurs (import failure, mapping corruption, disk full). The user believes anonymization is active when it is not. **False sense of security.**

**Remediation**: Log errors to stderr. Consider returning a "deny" permission decision rather than falling through to unmasked content. At minimum, write to a hook error log at `~/.cloudmask/hooks/hook-errors.log`.

---

### [CRITICAL] src/cloudmask/mapper.py:46 + ~/.cloudmask/hooks/mapping.json
**Category**: security
**R_i**: 9.00 | **Reviewers**: Security(7), SecurityDeepDive(9) (k=2)

**Description**: The mapping.json file is a **complete plaintext oracle** — it contains every original-to-anonymized mapping. Anyone who reads this single file can reverse all anonymization without knowing the seed. It is stored at a predictable path with no encryption and no explicit permission hardening from the hook code path.

**Remediation**: Encrypt mapping.json at rest using the existing `encrypt_mapping`/`decrypt_mapping` infrastructure in `utils/security.py`. Ensure `~/.cloudmask/hooks/mapping.json` gets 0600 permissions. Consider storing only forward hashes (not reversible mappings) for the hook path.

---

### [CRITICAL] scripts/hooks/mask-hook.py:147 + src/cloudmask/__init__.py
**Category**: performance
**R_i**: 9.00 | **Reviewers**: Performance(9+8) (k=2)

**Description**: Every hook invocation spawns a new Python process (30-80ms startup) and imports the entire `cloudmask` package via `__init__.py`, which eagerly loads ~20 submodules including `cryptography` (50-150ms), `PyYAML` (20-40ms), streaming, ratelimit, config_templates, etc. **Total overhead: 130-380ms per file operation**, compounding severely during multi-file sessions.

**Remediation**: (1) Implement lazy imports in `__init__.py` using `__getattr__`-based deferred loading. (2) Have the hook import only `from cloudmask.core import CloudMask` or even deeper: `from cloudmask.anonymizer import Anonymizer`. (3) Long-term: replace per-invocation process spawn with a persistent daemon communicating via Unix domain socket.

---

## High Findings (Severity 7-8)

### [HIGH] scripts/hooks/mask-hook.py:51 — Weak Default Seed
**Category**: security | **R_i**: 8.00 | **Reviewers**: Security(7), SecurityDeepDive(8), Reliability(5), Maintainability(6) (k=4)

Hardcoded `"claude-hook-default-seed"` is publicly visible in source code. All anonymization without an explicit seed is trivially reversible.

**Remediation**: Refuse to run if CLOUDMASK_SEED is not set. Remove the fallback.

---

### [HIGH] scripts/hooks/mask-hook.py:168 — Stale Shadow Misdirection
**Category**: reliability | **R_i**: 8.00 | **Reviewers**: Reliability(8), Correctness(6) (k=2)

`_handle_write_or_edit` redirects writes to shadow if it exists, regardless of freshness. If real file was modified externally (git pull, editor), the shadow is stale. Claude's edit + demask overwrites the real file with stale content, **silently destroying external changes**.

**Remediation**: Compare mtime of real vs shadow. If real is newer, re-anonymize before redirecting. Store original file hash alongside shadow for freshness validation.

---

### [HIGH] scripts/hooks/demask-hook.py:116 — Non-Atomic Real File Write
**Category**: reliability | **R_i**: 7.20 | **Reviewers**: Reliability(8) (k=1)

`real.write_text()` can be interrupted mid-write, leaving the real file truncated or corrupt. mapper.py uses atomic writes but demask-hook does not.

**Remediation**: Write to tempfile, then `os.replace()` to target path.

---

### [HIGH] scripts/hooks/mask-hook.py:148 — New Instance Per Invocation
**Category**: performance | **R_i**: 7.20 | **Reviewers**: Performance(8) (k=1)

Each hook call creates a new CloudMask + Config + Anonymizer, loads mapping JSON, anonymizes, and writes mapping back. For sessions with hundreds of file operations, the mapping file is read/parsed/written hundreds of times with no caching.

**Remediation**: Skip `save_mapping` if mapping didn't change. Consider long-running daemon for warm state.

---

### [HIGH] scripts/install-hooks.py:74 — Low Seed Entropy (32-bit)
**Category**: security | **R_i**: 6.30 | **Reviewers**: SecurityDeepDive(7) (k=1)

Generated seeds are 8-char hex (32 bits entropy). Brute-forceable in minutes on GPU.

**Remediation**: Use `secrets.token_hex(32)` for 256-bit entropy. Minimum 128 bits for auto-generated seeds.

---

### [HIGH] scripts/install-hooks.py:39 — Seed Stored in Plaintext
**Category**: security | **R_i**: 7.00 | **Reviewers**: SecurityDeepDive(7) (k=1)

CLOUDMASK_SEED in `~/.claude/settings.json` env block. Any process reading this file can fully reverse anonymization.

**Remediation**: Store in system keychain or dedicated 0600-permission file. Set 0600 on settings.json.

---

### [HIGH] scripts/hooks/mask-hook.py:37 — Hook Bypass Channels
**Category**: security | **R_i**: 6.30 | **Reviewers**: SecurityDeepDive(7) (k=1)

Grep results, Bash output (`cat`, `terraform plan`, `aws` CLI), and user prompts reach Claude unmasked. Multiple common workflows bypass hooks entirely.

**Remediation**: Document prominently. Consider Bash/Grep PreToolUse hooks for output scanning.

---

### [HIGH] scripts/hooks/demask-hook.py:81 — O(N*M) Unanonymize
**Category**: performance | **R_i**: 6.30 | **Reviewers**: Performance(7) (k=1)

Up to 5 passes x N mapping entries x M text length = O(5*N*M). With 1000 entries and 100KB file: ~500M character comparisons.

**Remediation**: Build single-pass regex from all tokens. Resolve chains in mapping dict before text replacement.

---

### [HIGH] src/cloudmask/anonymizer.py:125 — ARN Re-Anonymization
**Category**: correctness | **R_i**: 5.60 | **Reviewers**: Correctness(7) (k=1)

When anonymizing ARNs, inner resource IDs and account IDs are anonymized separately, producing generated values that could be re-matched by patterns in subsequent calls. The mapping cache prevents double-anonymization of exact strings but not partial overlaps in generated hashes.

**Remediation**: Use placeholder format that cannot be re-matched by any pattern (e.g., `ANON-xxx` prefix).

---

### [HIGH] scripts/hooks/demask-hook.py:115 — Path Traversal in Write
**Category**: security | **R_i**: 6.30 | **Reviewers**: Security(6), SecurityDeepDive(6), Reliability(7) (k=3)

Shadow-to-real path derivation has no traversal protection. Symlinks in shadow directory could cause writes to arbitrary paths.

**Remediation**: Use `Path.resolve()` and validate against SHADOW_ROOT with `relative_to()`.

---

### [HIGH] src/cloudmask/mapper.py:114 — Dead isinstance Guard
**Category**: correctness | **R_i**: 8.00 | **Reviewers**: Correctness(8), Maintainability(6), Reliability(6) (k=3)

`isinstance(e, (FileOperationError, MappingError))` inside `except OSError` is dead code — those exceptions don't inherit from OSError and will never be caught by that handler.

**Remediation**: Restructure: wrap only lock acquisition in try/except OSError. Let `_save_inner` exceptions propagate naturally.

---

### [HIGH] scripts/hooks/mask-hook.py:149 — Mapping Race Condition
**Category**: reliability | **R_i**: 5.60 | **Reviewers**: Reliability(7) (k=1)

Concurrent hook invocations (Claude reads two files) load mapping independently, both add entries, and second save overwrites first's new entries.

**Remediation**: Use flock around entire load-anonymize-save sequence.

---

### [HIGH] scripts/hooks/mask-hook.py:49 — Duplicated Constants
**Category**: maintainability | **R_i**: 7.00 | **Reviewers**: Maintainability(7) (k=1)

SHADOW_ROOT, MAPPING_PATH, and AWS prefix list are duplicated across 3 files. Any path/pattern change must be updated in 3 locations.

**Remediation**: Extract to shared module or generate at install time.

---

## Moderate Findings (Severity 4-6) — Summary

| # | File | Line | Category | Sev | Description |
|---|------|------|----------|-----|-------------|
| 1 | anonymizer.py | 44 | security | 6 | SHA-256 truncated to 64 bits; HMAC-SHA256 recommended |
| 2 | anonymizer.py | 44 | security | 6 | Hash concatenation ambiguity (`seed:prefix:value`) |
| 3 | anonymizer.py | 71 | correctness | 5 | Generated account IDs can be re-matched |
| 4 | anonymizer.py | 76 | correctness | 4 | Generated IPs not in RFC 5737 reserved range |
| 5 | anonymizer.py | 80 | correctness | 3 | Double "domain-" prefix in generated domains |
| 6 | anonymizer.py | 60 | correctness | 3 | Double "company-" prefix in company hash |
| 7 | anonymizer.py | 89 | performance | 4 | `known` set re-allocated per call |
| 8 | anonymizer.py | 148 | performance | 6 | 7+ full-text regex scans per file |
| 9 | anonymizer.py | 25 | security | 5 | Custom regex ReDoS risk |
| 10 | mapper.py | 55 | performance | 6 | Dict merge creates full copy |
| 11 | mapper.py | 72 | performance | 5 | Indented JSON 2-3x larger than compact |
| 12 | mapper.py | 24 | performance | 4 | seed_hash recomputed per call |
| 13 | core.py | 20 | correctness | 5 | Empty string seed `""` silently replaced |
| 14 | core.py | 160 | correctness | 5 | Nested lists not anonymized |
| 15 | core.py | 95 | performance | 5 | CloudUnmask sorts on every call |
| 16 | core.py | 66 | maintainability | 5 | Lazy imports obscure dependencies |
| 17 | core.py | 126 | maintainability | 4 | TemporaryMask.__exit__ no cleanup |
| 18 | core.py | 130 | maintainability | 4 | 3 different default seeds across codebase |
| 19 | core.py | 41 | maintainability | 5 | Manual bidirectional state sync |
| 20 | demask-hook.py | 69 | correctness | 5 | Fragile mapping format detection |
| 21 | demask-hook.py | 74 | maintainability | 6 | Duplicated unanonymize logic vs core.py |
| 22 | demask-hook.py | 82 | maintainability | 5 | Magic number 5 for max passes |
| 23 | demask-hook.py | 68 | performance | 4 | Reverse mapping rebuilt every call |
| 24 | mask-hook.py | 130 | correctness | 4 | Extensionless files bypass filter |
| 25 | mask-hook.py | 158 | security | 6 | Shadow files world-readable (default umask) |
| 26 | mask-hook.py | 89 | performance | 3 | Quick-scan single-letter prefixes cause false positives |
| 27 | install-hooks.py | 49 | security | 4 | Shell metacharacters in path (no quoting) |
| 28 | install-hooks.py | 163 | security | 5 | settings.json/backup no 0600 permissions |
| 29 | install-hooks.py | 244 | security | 5 | Hook files 0755 not 0700 |
| 30 | install-hooks.py | 295 | maintainability | 3 | `any([...])` creates unnecessary list |

---

## Consensus Score Calculation

```
Inputs:
  R_bar  = 4.38  (mean R_i across 55 unique findings)
  R_max  = 10.00 (demask-hook.py:117 silent data loss)
  k      = 9     (security-category cross-reviewer agreements)
  n      = 6     (reviewers spawned)

Base formula:
  CS = (0.5 * 4.38) + (0.3 * 4.38 * (9/6)) + (0.2 * 10.00)
     = 2.19 + 1.97 + 2.00
     = 6.16

Minority protection triggered:
  4 findings with severity >= 9 AND confidence >= 8:
    - demask-hook.py:117  (sev=10, conf=10)  Reliability
    - mask-hook.py:164    (sev=9,  conf=10)  Reliability
    - mapper.py:46        (sev=9,  conf=10)  SecurityDeepDive
    - mask-hook.py:147    (sev=9,  conf=10)  Performance

  CS = max(6.16, 8.50) = 8.50
```

---

## Summary

The CloudMask hook system has **4 critical issues** that must be fixed before production use:

1. **Silent data loss**: Both hooks swallow all exceptions with bare `except: pass/return`, meaning users have zero visibility when masking/demasking fails. The demask-hook's silent failure is the most severe — Claude's edits are lost in the shadow file with no notification.

2. **Plaintext mapping oracle**: The mapping file at a predictable path contains every original-to-anonymized relationship in unencrypted JSON. This is the single point of failure for the entire anonymization scheme.

3. **Performance overhead**: Each file operation adds 130-380ms latency due to Python startup + eager import of the entire cloudmask package (including cryptography, yaml, and 20+ submodules). This compounds to seconds of delay during multi-file operations.

4. **Weak seed defaults**: The hardcoded default seed, 32-bit generated seeds, and plaintext seed storage collectively undermine the cryptographic foundation of the anonymization.

Secondary concerns include stale shadow file detection, non-atomic file writes, race conditions in concurrent mapping access, and path traversal in shadow-to-real path construction.
