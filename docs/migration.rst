Migration Guide
===============

This guide helps you migrate between CloudMask versions and upgrade your usage patterns.

Version Migration
-----------------

From 0.0.x to 0.1.0
~~~~~~~~~~~~~~~~~~~

**Breaking Changes:**

None - 0.1.0 is the initial stable release.

**New Features:**

* Encrypted mapping support
* Rate limiting
* Security enhancements
* Comprehensive testing

**Migration Steps:**

No migration needed for new installations.

Future Versions
~~~~~~~~~~~~~~~

This section will be updated with migration guides for future versions.

Configuration Migration
-----------------------

Legacy Configuration Format
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you were using an older configuration format, migrate to the current YAML schema:

**Old Format** (if you had custom scripts):

.. code-block:: python

   # Old way
   mask = CloudMask(
       seed="test",
       company_names=["Acme"],
       preserve_prefixes=True
   )

**New Format** (recommended):

.. code-block:: yaml

   # cloudmask.yaml
   company_names:
     - Acme Corp

   preserve_prefixes: true
   anonymize_ips: true
   seed: test

.. code-block:: python

   # New way
   from cloudmask import Config, CloudMask
   from pathlib import Path

   config = Config.from_yaml(Path("cloudmask.yaml"))
   mask = CloudMask(config=config)

Mapping File Migration
----------------------

Unencrypted to Encrypted
~~~~~~~~~~~~~~~~~~~~~~~~~

Migrate existing unencrypted mappings to encrypted format:

.. code-block:: python

   import json
   from cloudmask import save_encrypted_mapping

   # Load old unencrypted mapping
   with open("mapping.json") as f:
       mapping = json.load(f)

   # Save as encrypted
   save_encrypted_mapping(
       mapping,
       "mapping.enc",
       password="strong-password"
   )

   # Securely delete old file
   import os
   os.remove("mapping.json")

Mapping Format Changes
~~~~~~~~~~~~~~~~~~~~~~

If mapping format changes in future versions, use this pattern:

.. code-block:: python

   def migrate_mapping_v1_to_v2(old_mapping):
       """Migrate mapping from v1 to v2 format."""
       new_mapping = {}
       for key, value in old_mapping.items():
           # Apply transformation
           new_mapping[key] = transform(value)
       return new_mapping

   # Load old mapping
   with open("mapping-v1.json") as f:
       old_mapping = json.load(f)

   # Migrate
   new_mapping = migrate_mapping_v1_to_v2(old_mapping)

   # Save new format
   with open("mapping-v2.json", "w") as f:
       json.dump(new_mapping, f)

API Migration
-------------

Function Signature Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~

If function signatures change in future versions:

**Old API:**

.. code-block:: python

   # Hypothetical old API
   from cloudmask import anonymize_text
   result = anonymize_text(text, seed)

**New API:**

.. code-block:: python

   # Current API
   from cloudmask import anonymize
   result, mapping = anonymize(text, seed=seed)

Deprecated Features
~~~~~~~~~~~~~~~~~~~

Check for deprecation warnings:

.. code-block:: python

   import warnings

   # Enable all warnings
   warnings.simplefilter("always", DeprecationWarning)

   from cloudmask import CloudMask
   mask = CloudMask(seed="test")

CLI Migration
-------------

Command Changes
~~~~~~~~~~~~~~~

If CLI commands change in future versions:

**Old Commands:**

.. code-block:: bash

   # Hypothetical old commands
   cloudmask -a input.txt -o output.txt

**New Commands:**

.. code-block:: bash

   # Current commands
   cloudmask anonymize -i input.txt -o output.txt -m mapping.json

Update Scripts
~~~~~~~~~~~~~~

Update shell scripts to use new CLI:

.. code-block:: bash

   #!/bin/bash
   # Old script
   # cloudmask -a "$1" -o "$2"

   # New script
   cloudmask anonymize -i "$1" -o "$2" -m mapping.json

Seed Management Migration
--------------------------

Hardcoded to Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Migrate from hardcoded seeds to environment variables:

**Old Approach:**

.. code-block:: python

   # Bad - hardcoded seed
   mask = CloudMask(seed="my-secret-seed")

**New Approach:**

.. code-block:: python

   # Good - environment variable
   import os
   mask = CloudMask(seed=os.environ["CLOUDMASK_SEED"])

.. code-block:: bash

   # Set in environment
   export CLOUDMASK_SEED="my-secret-seed"

Environment to Secrets Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Migrate from environment variables to AWS Secrets Manager:

**Old Approach:**

.. code-block:: python

   import os
   seed = os.environ["CLOUDMASK_SEED"]

**New Approach:**

.. code-block:: python

   import boto3
   import json

   def get_seed_from_secrets_manager():
       client = boto3.client('secretsmanager')
       response = client.get_secret_value(SecretId='cloudmask/seed')
       secret = json.loads(response['SecretString'])
       return secret['seed']

   seed = get_seed_from_secrets_manager()
   mask = CloudMask(seed=seed)

Batch Processing Migration
---------------------------

Sequential to Batch
~~~~~~~~~~~~~~~~~~~

Migrate from sequential processing to batch processing:

**Old Approach:**

.. code-block:: python

   # Sequential processing
   results = []
   for text in texts:
       mask = CloudMask(seed="test")  # Creating new instance each time
       result = mask.anonymize(text)
       results.append(result)

**New Approach:**

.. code-block:: python

   # Batch processing
   mask = CloudMask(seed="test")  # Reuse instance
   results = []
   for text in texts:
       result = mask.anonymize(text)
       results.append(result)

   # Save single mapping
   mask.save_mapping("batch-mapping.json")

Add Rate Limiting
~~~~~~~~~~~~~~~~~

Add rate limiting to existing batch processing:

.. code-block:: python

   from cloudmask import CloudMask, BatchRateLimiter

   # Add rate limiter
   limiter = BatchRateLimiter(max_operations=1000, time_window=60)
   mask = CloudMask(seed="test", rate_limiter=limiter)

   for text in texts:
       result = mask.anonymize(text)

Testing Migration
-----------------

Update Test Cases
~~~~~~~~~~~~~~~~~

Update tests for new API:

**Old Tests:**

.. code-block:: python

   def test_anonymize():
       result = anonymize_text("vpc-123", "test")
       assert result != "vpc-123"

**New Tests:**

.. code-block:: python

   def test_anonymize():
       result, mapping = anonymize("vpc-123", seed="test")
       assert result != "vpc-123"
       assert "vpc-123" in mapping

Add Security Tests
~~~~~~~~~~~~~~~~~~

Add tests for new security features:

.. code-block:: python

   def test_encrypted_mapping():
       from cloudmask import save_encrypted_mapping, load_encrypted_mapping

       mapping = {"vpc-123": "vpc-abc"}
       save_encrypted_mapping(mapping, "test.enc", password="test")
       loaded = load_encrypted_mapping("test.enc", password="test")

       assert loaded == mapping

Deployment Migration
--------------------

Local to Production
~~~~~~~~~~~~~~~~~~~

Migrate from local development to production:

**Development:**

.. code-block:: python

   # Simple seed
   mask = CloudMask(seed="dev-seed")

**Production:**

.. code-block:: python

   # Secure seed from secrets manager
   import boto3
   import json

   def get_production_seed():
       client = boto3.client('secretsmanager')
       response = client.get_secret_value(SecretId='prod/cloudmask/seed')
       return json.loads(response['SecretString'])['seed']

   mask = CloudMask(seed=get_production_seed())

Add Monitoring
~~~~~~~~~~~~~~

Add monitoring to production deployments:

.. code-block:: python

   import logging
   from cloudmask import CloudMask

   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('cloudmask.log'),
           logging.StreamHandler()
       ]
   )

   logger = logging.getLogger(__name__)

   mask = CloudMask(seed=seed)
   logger.info("CloudMask initialized")

   result = mask.anonymize(text)
   logger.info(f"Anonymized {len(text)} characters")

Rollback Procedures
-------------------

Version Rollback
~~~~~~~~~~~~~~~~

If you need to rollback to a previous version:

.. code-block:: bash

   # Uninstall current version
   pip uninstall cloudmask

   # Install specific version
   pip install cloudmask==0.0.9

Mapping Rollback
~~~~~~~~~~~~~~~~

Keep backups of mapping files:

.. code-block:: python

   import shutil
   from datetime import datetime

   # Backup before changes
   timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
   shutil.copy("mapping.json", f"mapping.json.backup.{timestamp}")

   # If rollback needed
   shutil.copy("mapping.json.backup.20240101_120000", "mapping.json")

Configuration Rollback
~~~~~~~~~~~~~~~~~~~~~~

Version control your configuration:

.. code-block:: bash

   # Initialize git for config
   git init
   git add cloudmask.yaml
   git commit -m "Initial config"

   # After changes
   git add cloudmask.yaml
   git commit -m "Updated config"

   # Rollback if needed
   git checkout HEAD~1 cloudmask.yaml

Best Practices for Migration
-----------------------------

1. **Test First**: Test migration in development environment
2. **Backup Everything**: Backup mappings, configs, and data
3. **Gradual Migration**: Migrate incrementally, not all at once
4. **Monitor**: Watch for errors after migration
5. **Document**: Document your migration process
6. **Rollback Plan**: Have a rollback plan ready
7. **Validate**: Validate data after migration

Migration Checklist
-------------------

Pre-Migration
~~~~~~~~~~~~~

- [ ] Read release notes
- [ ] Review breaking changes
- [ ] Backup all mapping files
- [ ] Backup configuration files
- [ ] Test in development environment
- [ ] Document current setup
- [ ] Prepare rollback plan

During Migration
~~~~~~~~~~~~~~~~

- [ ] Update CloudMask version
- [ ] Update configuration format
- [ ] Migrate mapping files
- [ ] Update code/scripts
- [ ] Update tests
- [ ] Update documentation

Post-Migration
~~~~~~~~~~~~~~

- [ ] Run test suite
- [ ] Validate anonymization
- [ ] Verify unanonymization
- [ ] Check performance
- [ ] Monitor for errors
- [ ] Update team documentation
- [ ] Archive old backups

Support
-------

If you encounter issues during migration:

1. Check the :doc:`troubleshooting` guide
2. Search GitHub issues
3. Create a migration issue with:

   * Source version
   * Target version
   * Migration steps taken
   * Error messages
   * Expected vs actual behavior

We're here to help make your migration smooth!
