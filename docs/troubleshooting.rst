Troubleshooting Guide
=====================

Common Issues
-------------

Installation Issues
~~~~~~~~~~~~~~~~~~~

**Problem**: ``pip install cloudmask`` fails

**Solutions**:

1. Check Python version:

   .. code-block:: bash

      python --version  # Must be 3.10+

2. Upgrade pip:

   .. code-block:: bash

      python -m pip install --upgrade pip

3. Use uv instead:

   .. code-block:: bash

      uv pip install cloudmask

**Problem**: Import error after installation

**Solutions**:

1. Verify installation:

   .. code-block:: bash

      pip list | grep cloudmask

2. Check virtual environment:

   .. code-block:: bash

      which python
      source .venv/bin/activate

3. Reinstall:

   .. code-block:: bash

      pip uninstall cloudmask
      pip install cloudmask

Configuration Issues
~~~~~~~~~~~~~~~~~~~~

**Problem**: ``Config.from_yaml()`` fails

**Solutions**:

1. Validate YAML syntax:

   .. code-block:: bash

      python -c "import yaml; yaml.safe_load(open('cloudmask.yaml'))"

2. Check file path:

   .. code-block:: python

      from pathlib import Path
      config_path = Path("cloudmask.yaml")
      print(f"Exists: {config_path.exists()}")
      print(f"Absolute: {config_path.absolute()}")

3. Verify schema:

   .. code-block:: yaml

      # Required fields
      company_names: []  # Can be empty list
      custom_patterns: []  # Can be empty list

**Problem**: Custom regex pattern fails

**Solutions**:

1. Test regex separately:

   .. code-block:: python

      import re
      pattern = r'\bTICKET-\d+'
      re.compile(pattern)  # Should not raise

2. Escape special characters:

   .. code-block:: yaml

      custom_patterns:
        - pattern: '\\bTICKET-\\d+'  # Double backslash in YAML
          name: ticket

3. Use raw strings in Python:

   .. code-block:: python

      from cloudmask import CustomPattern
      pattern = CustomPattern(pattern=r'\bTICKET-\d+', name='ticket')

Anonymization Issues
~~~~~~~~~~~~~~~~~~~~

**Problem**: Some IDs not anonymized

**Solutions**:

1. Check pattern matching:

   .. code-block:: python

      import re
      text = "vpc-123"
      pattern = r'\bvpc-[a-f0-9]+'
      matches = re.findall(pattern, text)
      print(f"Matches: {matches}")

2. Verify configuration:

   .. code-block:: python

      mask = CloudMask(seed="test")
      print(f"Anonymize IPs: {mask.config.anonymize_ips}")
      print(f"Preserve prefixes: {mask.config.preserve_prefixes}")

3. Enable debug logging:

   .. code-block:: python

      import logging
      logging.basicConfig(level=logging.DEBUG)

      from cloudmask import CloudMask
      mask = CloudMask(seed="test")
      result = mask.anonymize("vpc-123")

**Problem**: Anonymized output looks wrong

**Solutions**:

1. Check seed consistency:

   .. code-block:: python

      # Same seed = same output
      mask1 = CloudMask(seed="test")
      mask2 = CloudMask(seed="test")

      result1 = mask1.anonymize("vpc-123")
      result2 = mask2.anonymize("vpc-123")

      assert result1 == result2

2. Verify prefix preservation:

   .. code-block:: python

      mask = CloudMask(seed="test")
      result = mask.anonymize("vpc-123")
      assert result.startswith("vpc-")

Unanonymization Issues
~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Unanonymization doesn't restore original

**Solutions**:

1. Verify mapping file:

   .. code-block:: python

      import json
      with open("mapping.json") as f:
          mapping = json.load(f)
      print(f"Mapping entries: {len(mapping)}")

2. Check mapping consistency:

   .. code-block:: python

      from cloudmask import CloudMask, CloudUnmask

      mask = CloudMask(seed="test")
      anonymized = mask.anonymize("vpc-123")

      unmask = CloudUnmask(mapping=mask.mapping)
      original = unmask.unanonymize(anonymized)

      assert original == "vpc-123"

3. Ensure complete anonymization:

   .. code-block:: python

      # Save mapping immediately after anonymization
      mask = CloudMask(seed="test")
      anonymized = mask.anonymize(text)
      mask.save_mapping("mapping.json")  # Don't forget this!

**Problem**: Encrypted mapping won't decrypt

**Solutions**:

1. Verify password:

   .. code-block:: python

      from cloudmask import load_encrypted_mapping

      try:
          mapping = load_encrypted_mapping("mapping.enc", password="wrong")
      except Exception as e:
          print(f"Error: {e}")

2. Check file integrity:

   .. code-block:: bash

      # File should not be corrupted
      file mapping.enc
      ls -lh mapping.enc

3. Re-encrypt if needed:

   .. code-block:: python

      from cloudmask import save_encrypted_mapping, load_encrypted_mapping

      # Load with old password
      mapping = load_encrypted_mapping("mapping.enc", password="old")

      # Save with new password
      save_encrypted_mapping(mapping, "mapping-new.enc", password="new")

CLI Issues
~~~~~~~~~~

**Problem**: ``cloudmask`` command not found

**Solutions**:

1. Check installation:

   .. code-block:: bash

      pip show cloudmask

2. Verify PATH:

   .. code-block:: bash

      which cloudmask
      echo $PATH

3. Use module syntax:

   .. code-block:: bash

      python -m cloudmask.cli anonymize -i input.txt -o output.txt

**Problem**: Clipboard operations fail

**Solutions**:

1. Install clipboard support:

   .. code-block:: bash

      # macOS - should work by default
      # Linux
      sudo apt-get install xclip
      # Windows - should work by default

2. Test clipboard:

   .. code-block:: python

      import pyperclip
      pyperclip.copy("test")
      print(pyperclip.paste())

3. Use file operations instead:

   .. code-block:: bash

      cloudmask anonymize -i input.txt -o output.txt -m mapping.json

Performance Issues
~~~~~~~~~~~~~~~~~~

**Problem**: Slow processing of large files

**Solutions**:

1. Use batch processing:

   .. code-block:: python

      from cloudmask import CloudMask

      mask = CloudMask(seed="test")

      # Process in chunks
      chunk_size = 1024 * 1024  # 1MB
      with open("large.txt") as f:
          while chunk := f.read(chunk_size):
              result = mask.anonymize(chunk)

2. Optimize regex patterns:

   .. code-block:: python

      # Compile patterns once
      import re
      pattern = re.compile(r'\bvpc-[a-f0-9]+')

      # Reuse compiled pattern
      matches = pattern.findall(text)

3. Monitor memory usage:

   .. code-block:: python

      import tracemalloc

      tracemalloc.start()
      mask = CloudMask(seed="test")
      result = mask.anonymize(large_text)

      current, peak = tracemalloc.get_traced_memory()
      print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")

**Problem**: Rate limiting too restrictive

**Solutions**:

1. Adjust limits:

   .. code-block:: python

      from cloudmask import CloudMask, BatchRateLimiter

      # Increase limits
      limiter = BatchRateLimiter(
          max_operations=10000,  # More operations
          time_window=60  # Per minute
      )
      mask = CloudMask(seed="test", rate_limiter=limiter)

2. Disable rate limiting:

   .. code-block:: python

      # For trusted environments only
      mask = CloudMask(seed="test", rate_limiter=None)

Error Messages
--------------

ValueError: Invalid seed
~~~~~~~~~~~~~~~~~~~~~~~~

**Cause**: Seed is None or empty

**Solution**:

.. code-block:: python

   # Provide a seed
   mask = CloudMask(seed="my-secret-seed")

   # Or use environment variable
   import os
   mask = CloudMask(seed=os.environ.get("CLOUDMASK_SEED", "default"))

FileNotFoundError: Config file not found
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause**: Configuration file path is incorrect

**Solution**:

.. code-block:: python

   from pathlib import Path

   config_path = Path("cloudmask.yaml")
   if not config_path.exists():
       print(f"Config not found at: {config_path.absolute()}")
       # Create default config
       from cloudmask import Config
       config = Config()
       config.to_yaml(config_path)

JSONDecodeError: Invalid mapping file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause**: Mapping file is corrupted or invalid JSON

**Solution**:

.. code-block:: python

   import json

   try:
       with open("mapping.json") as f:
           mapping = json.load(f)
   except json.JSONDecodeError as e:
       print(f"Invalid JSON at line {e.lineno}: {e.msg}")
       # Restore from backup or re-anonymize

RuntimeError: Rate limit exceeded
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause**: Too many operations in time window

**Solution**:

.. code-block:: python

   import time
   from cloudmask import CloudMask

   mask = CloudMask(seed="test")

   for text in large_dataset:
       try:
           result = mask.anonymize(text)
       except RuntimeError:
           print("Rate limit hit, waiting...")
           time.sleep(60)  # Wait for window to reset
           result = mask.anonymize(text)

Debugging Tips
--------------

Enable Debug Logging
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import logging

   logging.basicConfig(
       level=logging.DEBUG,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )

   from cloudmask import CloudMask
   mask = CloudMask(seed="test")

Inspect Mappings
~~~~~~~~~~~~~~~~

.. code-block:: python

   from cloudmask import CloudMask

   mask = CloudMask(seed="test")
   result = mask.anonymize("vpc-123 i-456")

   # Inspect mapping
   print("Mapping:")
   for original, anonymized in mask.mapping.items():
       print(f"  {original} -> {anonymized}")

Test Patterns
~~~~~~~~~~~~~

.. code-block:: python

   import re

   # Test AWS resource ID pattern
   pattern = r'\b(vpc|subnet|sg|i|ami|vol|snap)-[a-f0-9]+'
   text = "vpc-123 subnet-456 invalid-789"

   matches = re.findall(pattern, text)
   print(f"Matches: {matches}")

Verify Installation
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import cloudmask

   print(f"Version: {cloudmask.__version__}")
   print(f"Location: {cloudmask.__file__}")
   print(f"Exports: {cloudmask.__all__}")

Getting Help
------------

Check Documentation
~~~~~~~~~~~~~~~~~~~

* Read the :doc:`usage` guide
* Review :doc:`api` reference
* Check :doc:`security` considerations

Search Issues
~~~~~~~~~~~~~

Search existing issues on GitHub:

https://github.com/yourusername/cloudmask/issues

Create Issue
~~~~~~~~~~~~

If you can't find a solution:

1. Check if issue already exists
2. Gather information:

   * Python version
   * CloudMask version
   * Operating system
   * Error messages
   * Minimal reproduction

3. Create detailed issue with:

   * Clear title
   * Steps to reproduce
   * Expected vs actual behavior
   * Code samples
   * Error logs

Community Support
~~~~~~~~~~~~~~~~~

* GitHub Discussions: https://github.com/yourusername/cloudmask/discussions
* Stack Overflow: Tag with ``cloudmask``

Diagnostic Script
-----------------

Run this script to gather diagnostic information:

.. code-block:: python

   import sys
   import platform

   print("=== CloudMask Diagnostics ===")
   print(f"Python: {sys.version}")
   print(f"Platform: {platform.platform()}")

   try:
       import cloudmask
       print(f"CloudMask: {cloudmask.__version__}")
   except ImportError as e:
       print(f"CloudMask: NOT INSTALLED ({e})")

   try:
       import yaml
       print(f"PyYAML: {yaml.__version__}")
   except ImportError:
       print("PyYAML: NOT INSTALLED")

   try:
       import pyperclip
       print("pyperclip: INSTALLED")
   except ImportError:
       print("pyperclip: NOT INSTALLED")

   try:
       import cryptography
       print(f"cryptography: {cryptography.__version__}")
   except ImportError:
       print("cryptography: NOT INSTALLED")

   print("\n=== Test Anonymization ===")
   try:
       from cloudmask import anonymize
       text, mapping = anonymize("vpc-123", seed="test")
       print(f"Input: vpc-123")
       print(f"Output: {text}")
       print("Status: OK")
   except Exception as e:
       print(f"Status: FAILED - {e}")
