---
title: Test Plan for Review Findings Fix
created: 2026-03-11T11:00:00Z
---

# TEST-PLAN: Verify All 45 Tasks

## Testing Approach

- **Unit tests**: pytest for core library changes (anonymizer, mapper, core)
- **Integration tests**: End-to-end hook round-trip tests
- **Regression tests**: Existing test suite must pass (`pytest -o "addopts="`)
- **Property tests**: Verify each PROP-* observable

## Coverage Targets

- All modified functions must have at least 1 test
- Critical path (mask → shadow → demask → real) must have round-trip test
- Breaking changes (HMAC migration) must have migration test

---

## Test Cases

### TC-001: Lazy imports do not break public API
- **Tasks**: TASK-002
- **Properties**: PROP-011
- **Type**: unit
- **Steps**:
  1. `python -c "from cloudmask import CloudMask, Config, CloudUnmask; print('eager ok')"`
  2. `python -c "from cloudmask import encrypt_mapping, Storage, setup_logging; print('lazy ok')"`
  3. `python -c "import time; t=time.time(); from cloudmask.core import CloudMask; d=time.time()-t; assert d < 0.1, f'too slow: {d}s'"`
- **Expected**: All exit 0, deep import under 100ms

### TC-002: AWS_RESOURCE_PREFIXES is canonical
- **Tasks**: TASK-001, TASK-005
- **Properties**: PROP-009
- **Type**: unit
- **Steps**:
  1. `python -c "from cloudmask.utils.patterns import AWS_RESOURCE_PREFIXES; assert 'vpc' in AWS_RESOURCE_PREFIXES; assert len(AWS_RESOURCE_PREFIXES) == 25"`
  2. `grep -c '"vpc"' src/cloudmask/anonymizer.py` returns 0
- **Expected**: Prefix set has 25 entries, no duplicates in anonymizer

### TC-003: HMAC-based hashing produces different output than SHA-256
- **Tasks**: TASK-006
- **Properties**: PROP-010
- **Type**: unit
- **Steps**:
  1. Create Anonymizer with seed "test-seed-12345", anonymize "vpc-abc12345"
  2. Verify output differs from old SHA-256 concatenation scheme
  3. Verify same input + same seed produces same output (deterministic)
- **Expected**: Deterministic, different from old scheme

### TC-004: Generated IPs are in RFC 5737 range
- **Tasks**: TASK-006
- **Properties**: PROP-010
- **Type**: unit
- **Steps**:
  1. Anonymize a valid IP address (e.g., "10.0.1.5")
  2. Verify result starts with "198.51.100."
- **Expected**: All generated IPs in 198.51.100.0/24

### TC-005: No double prefix in domain anonymization
- **Tasks**: TASK-007
- **Properties**: none
- **Type**: unit
- **Steps**:
  1. Anonymize domain "example.com"
  2. Verify result matches pattern `domain-[a-f0-9]+\.com`
  3. Verify result does NOT contain "domain-domain-"
- **Expected**: Single "domain-" prefix

### TC-006: No double prefix in company anonymization
- **Tasks**: TASK-008
- **Properties**: none
- **Type**: unit
- **Steps**:
  1. Anonymize company name "Acme Corp"
  2. Verify result matches pattern `Company-[a-f0-9]+`
  3. Verify result does NOT contain "company-" substring
- **Expected**: "Company-" prefix only, no "company-" inside

### TC-007: Seed hash cached in MappingManager
- **Tasks**: TASK-011
- **Properties**: none
- **Type**: unit
- **Steps**:
  1. Create MappingManager with seed
  2. Verify `_seed_hash` attribute exists
  3. Call `_get_seed_hash()` twice, verify same value
- **Expected**: Cached, no recomputation

### TC-008: Save restructured — lock errors don't re-raise domain errors
- **Tasks**: TASK-012
- **Properties**: none
- **Type**: unit
- **Steps**:
  1. Call save() on a valid path — should succeed
  2. Call save() with invalid mapping (>1M entries placeholder check) — should raise MappingError
  3. Verify MappingError propagates, not OSError
- **Expected**: Domain exceptions propagate cleanly

### TC-009: Mask-hook refuses without CLOUDMASK_SEED
- **Tasks**: TASK-021
- **Properties**: PROP-004
- **Type**: integration
- **Steps**:
  1. Run mask-hook.py with CLOUDMASK_SEED unset
  2. Provide valid Read hook JSON on stdin
  3. Verify stderr contains "CLOUDMASK_SEED not set"
  4. Verify stdout is empty (no redirect)
- **Expected**: Hook refuses to mask, error on stderr

### TC-010: Mask-hook logs errors instead of swallowing
- **Tasks**: TASK-022
- **Properties**: PROP-002
- **Type**: integration
- **Steps**:
  1. Run mask-hook.py with valid CLOUDMASK_SEED but missing cloudmask package
  2. Verify stderr contains "mask-hook error"
  3. Verify stdout is empty
- **Expected**: Error logged, not silently swallowed

### TC-011: Demask-hook logs errors instead of swallowing
- **Tasks**: TASK-031
- **Properties**: PROP-001
- **Type**: integration
- **Steps**:
  1. Run demask-hook.py with corrupted mapping file
  2. Verify stderr contains "demask-hook error"
- **Expected**: Error logged, not silently swallowed

### TC-012: Atomic shadow write survives interrupt
- **Tasks**: TASK-025
- **Properties**: PROP-005
- **Type**: integration
- **Steps**:
  1. Create a real file with AWS identifiers
  2. Run mask-hook Read flow
  3. Verify shadow file exists with 0o600 permissions
  4. Verify shadow parent dir has 0o700 permissions
- **Expected**: Shadow created atomically with secure permissions

### TC-013: Atomic real file write in demask
- **Tasks**: TASK-032
- **Properties**: PROP-005
- **Type**: integration
- **Steps**:
  1. Create shadow file with anonymized content
  2. Run demask-hook Write flow
  3. Verify real file restored with 0o600 permissions
  4. Verify no temp files left behind
- **Expected**: Real file written atomically

### TC-014: Stale shadow detection
- **Tasks**: TASK-026
- **Properties**: PROP-006
- **Type**: integration
- **Steps**:
  1. Create real file, run mask-hook Read to create shadow
  2. Modify real file (touch with newer mtime)
  3. Run mask-hook Write/Edit flow
  4. Verify shadow was refreshed before redirect
- **Expected**: Shadow updated when real file is newer

### TC-015: Path traversal blocked in mask-hook
- **Tasks**: TASK-024
- **Properties**: PROP-003
- **Type**: unit
- **Steps**:
  1. Call _real_to_shadow with path containing ".."
  2. Verify ValueError raised (relative_to fails)
- **Expected**: Traversal attempt raises exception

### TC-016: Path traversal blocked in demask-hook
- **Tasks**: TASK-033
- **Properties**: PROP-003
- **Type**: unit
- **Steps**:
  1. Call _shadow_to_real with crafted shadow path containing symlinks
  2. Verify ValueError raised
- **Expected**: Traversal attempt raises exception

### TC-017: Mapping save skipped when unchanged
- **Tasks**: TASK-027
- **Properties**: PROP-012
- **Type**: integration
- **Steps**:
  1. Create mapping with known entries
  2. Anonymize text that contains only already-mapped values
  3. Verify save_mapping was NOT called (mapping_size_before == after)
- **Expected**: No unnecessary I/O

### TC-018: File locking in mask-hook
- **Tasks**: TASK-028
- **Properties**: PROP-007
- **Type**: integration
- **Steps**:
  1. Run mask-hook, verify lock file created
  2. Verify fcntl.flock called
- **Expected**: Lock acquired and released

### TC-019: Shared lock for demask-hook reads
- **Tasks**: TASK-034
- **Properties**: PROP-007
- **Type**: integration
- **Steps**:
  1. Run demask-hook, verify LOCK_SH used for mapping read
- **Expected**: Shared lock acquired

### TC-020: Seed entropy >= 128 bits
- **Tasks**: TASK-040
- **Properties**: PROP-013
- **Type**: unit
- **Steps**:
  1. Call _generate_seed_options()
  2. Verify all seeds are 32 chars (128 bits)
- **Expected**: Each seed is 32 hex characters

### TC-021: Settings.json written with 0600
- **Tasks**: TASK-042, TASK-043
- **Properties**: PROP-008
- **Type**: integration
- **Steps**:
  1. Run installer in test environment
  2. Verify settings.json has 0o600 permissions
  3. Verify hook files have 0o700 permissions
- **Expected**: Secure permissions on all files

### TC-022: Seed masked in status output
- **Tasks**: TASK-044
- **Properties**: none
- **Type**: unit
- **Steps**:
  1. Run `install-hooks.py --status`
  2. Verify full seed is NOT printed
  3. Verify partial seed (first 4 + last 4 with ...) is shown
- **Expected**: Seed partially masked

### TC-023: Full round-trip with all fixes
- **Tasks**: ALL
- **Properties**: PROP-001, PROP-002, PROP-005, PROP-006
- **Type**: e2e
- **Steps**:
  1. Install hooks with test seed
  2. Create .tf file with VPC IDs, account IDs, ARNs, IPs
  3. Simulate Read → verify shadow created with anonymized content
  4. Simulate Edit on shadow → verify shadow updated
  5. Simulate PostToolUse → verify real file restored with original values
  6. `diff original.tf restored.tf` returns empty
- **Expected**: Perfect round-trip, zero data loss

### TC-024: Existing test suite passes
- **Tasks**: ALL
- **Properties**: none
- **Type**: regression
- **Steps**:
  1. Run `pytest -o "addopts=" tests/`
  2. All tests pass
- **Expected**: No regressions

### TC-025: Mapping format detection robust
- **Tasks**: TASK-035, TASK-036
- **Properties**: none
- **Type**: unit
- **Steps**:
  1. Load mapping with `_metadata` but no `mappings` key → returns {}
  2. Load mapping with non-string values → filters them out
  3. Load mapping with old format (no metadata) → works correctly
- **Expected**: All edge cases handled without errors

### TC-026: Unanonymize convergence warning
- **Tasks**: TASK-037
- **Properties**: none
- **Type**: unit
- **Steps**:
  1. Create a mapping that requires > 5 passes to converge
  2. Run _unanonymize
  3. Verify stderr contains "did not converge"
- **Expected**: Warning emitted on non-convergence

### TC-027: Regex-based unanonymize produces same output
- **Tasks**: TASK-038
- **Properties**: none
- **Type**: unit
- **Steps**:
  1. Create mapping with 100 entries
  2. Anonymize text
  3. Unanonymize with new regex-based function
  4. Verify output matches original
- **Expected**: Functional equivalence with old str.replace approach

### TC-028: anonymize_dict handles nested lists
- **Tasks**: TASK-017
- **Properties**: none
- **Type**: unit
- **Steps**:
  1. Call anonymize_dict with `{"key": [["vpc-abc12345"]]}` (nested list)
  2. Verify inner string is anonymized
- **Expected**: Nested list strings anonymized

### TC-029: CloudUnmask pre-sorts in __init__
- **Tasks**: TASK-018
- **Properties**: none
- **Type**: unit
- **Steps**:
  1. Create CloudUnmask with mapping
  2. Verify `_sorted_replacements` attribute exists
  3. Verify it is sorted by key length descending
- **Expected**: Pre-sorted, unanonymize uses cached sort

### TC-030: TemporaryMask clears mapping on exit
- **Tasks**: TASK-019
- **Properties**: none
- **Type**: unit
- **Steps**:
  1. Use TemporaryMask context manager
  2. Anonymize text inside context
  3. After exiting, verify mask is None and mappings cleared
- **Expected**: Sensitive data cleared on exit
