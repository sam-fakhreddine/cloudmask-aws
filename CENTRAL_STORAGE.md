# Central Storage for CloudMask Mappings

CloudMask now stores mapping files in a central, secure location by default.

## Location

All mapping files are stored in:
```
~/.cloudmask/
```

## Security

- **Directory permissions**: `700` (owner read/write/execute only)
- **File permissions**: `600` (owner read/write only)
- Permissions are automatically set when files are created or accessed

## Usage

### CLI

The `-m/--mapping` flag is now optional. If not specified, mappings are stored in `~/.cloudmask/mapping.json`:

```bash
# Anonymize (uses ~/.cloudmask/mapping.json by default)
cloudmask anonymize --clipboard

# Unanonymize (uses ~/.cloudmask/mapping.json by default)
cloudmask unanonymize --clipboard

# You can still specify a custom location
cloudmask anonymize --clipboard -m /path/to/custom-mapping.json
```

### Python API

```python
from cloudmask import CloudMask, Storage

# Get the storage directory
storage_dir = Storage.Dir  # Returns: ~/.cloudmask

# Get the default mapping path
mapping_path = Storage.DefaultMappingPath  # Returns: ~/.cloudmask/mapping.json

# Use with CloudMask
mask = CloudMask()
anonymized = mask.anonymize("vpc-12345")
mask.save_mapping(Storage.DefaultMappingPath)  # Saves with secure permissions
```

## Benefits

1. **Centralized**: All mappings in one secure location
2. **Automatic**: No need to specify mapping path for common workflows
3. **Secure**: Proper file permissions set automatically
4. **Convenient**: Works seamlessly with clipboard operations
5. **Safe**: Mappings are merged, never overwritten - your data is preserved

## Migration

If you have existing mapping files, you can:

1. Move them to `~/.cloudmask/` manually
2. Continue using custom paths with the `-m` flag
3. Let CloudMask create new mappings in the default location

## Mapping Preservation & Seed Verification

✓ **Mappings are automatically merged**: When you save to an existing mapping file, new mappings are added to existing ones. Your previous mappings are never lost.

✓ **Seed verification**: CloudMask tracks which seed was used to create mappings. You can only merge mappings created with the same seed, preventing data corruption.

```python
# First anonymization
mask1 = CloudMask(seed="production-seed")
mask1.anonymize("vpc-11111")
mask1.save_mapping(Storage.DefaultMappingPath)  # Saves 1 mapping

# Second anonymization with SAME seed
mask2 = CloudMask(seed="production-seed")
mask2.anonymize("vpc-22222")
mask2.save_mapping(Storage.DefaultMappingPath)  # Now has 2 mappings (merged!)

# Different seed - will fail
mask3 = CloudMask(seed="different-seed")
mask3.anonymize("vpc-33333")
mask3.save_mapping(Storage.DefaultMappingPath)  # ERROR: Cannot merge different seeds
```

To overwrite instead of merge:
```python
mask.save_mapping(path, merge=False)  # Overwrites existing file
```

**Important**: Always use the same seed for a given project/environment. Different seeds produce different anonymized values for the same input.

## Security Notes

⚠️ **Important**: The `~/.cloudmask/` directory contains sensitive mapping data.

- Keep this directory secure
- Don't share mapping files
- Consider encrypting mappings with `--encrypt` flag for extra security
- Back up mapping files if needed for long-term unanonymization
- Mappings grow over time - monitor file size
- Always use the same seed for a project to enable mapping merges
- Seed is stored as a hash in the mapping file for verification
