Usage Guide
===========

This guide provides detailed examples and tutorials for using CloudMask.

Basic Anonymization
-------------------

Simple Text Anonymization
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from cloudmask import anonymize, unanonymize

   text = "Instance i-1234567890abcdef0 in vpc-abc123"
   anonymized, mapping = anonymize(text, seed="my-seed")

   print(anonymized)
   # Output: Instance i-a1b2c3d4e5f6g7h8i in vpc-x9y8z7

   original = unanonymize(anonymized, mapping)
   assert original == text

With Company Names
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from cloudmask import anonymize

   text = "Acme Corp uses account 123456789012"
   anonymized, mapping = anonymize(
       text,
       seed="my-seed",
       company_names=["Acme Corp"]
   )

Advanced Usage
--------------

Using CloudMask Class
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from cloudmask import CloudMask, Config
   from pathlib import Path

   # Load custom config
   config = Config.from_yaml(Path("cloudmask.yaml"))

   # Create anonymizer
   mask = CloudMask(config=config, seed="production-seed")

   # Anonymize text
   result = mask.anonymize("vpc-123 i-456")

   # Save mapping
   mask.save_mapping("mapping.json")

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   from cloudmask import CloudMask
   from pathlib import Path

   mask = CloudMask(seed="batch-seed")

   # Process multiple files
   for file in Path("configs").glob("*.yaml"):
       output = Path("anonymized") / file.name
       mask.anonymize_file(file, output)

   # Single mapping for all files
   mask.save_mapping("master-mapping.json")

Context Manager
~~~~~~~~~~~~~~~

.. code-block:: python

   from cloudmask import TemporaryMask

   with TemporaryMask(seed="temp-seed") as mask:
       anonymized = mask.anonymize("vpc-123 i-456")
       # Process anonymized data
       # Mapping is discarded after context exits

Dictionary Anonymization
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from cloudmask import anonymize_dict

   data = {
       "instance_id": "i-1234567890abcdef0",
       "vpc_id": "vpc-abc123",
       "account": "123456789012"
   }

   anonymized, mapping = anonymize_dict(data, seed="my-seed")

Security Features
-----------------

Encrypted Mappings
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from cloudmask import CloudMask, save_encrypted_mapping, load_encrypted_mapping

   mask = CloudMask(seed="my-seed")
   anonymized = mask.anonymize("vpc-123")

   # Save encrypted mapping
   save_encrypted_mapping(
       mask.mapping,
       "mapping.enc",
       password="strong-password"
   )

   # Load encrypted mapping
   mapping = load_encrypted_mapping(
       "mapping.enc",
       password="strong-password"
   )

Rate Limiting
~~~~~~~~~~~~~

.. code-block:: python

   from cloudmask import CloudMask
   from cloudmask import BatchRateLimiter

   limiter = BatchRateLimiter(max_operations=1000, time_window=60)
   mask = CloudMask(seed="my-seed", rate_limiter=limiter)

   # Process with rate limiting
   for text in large_dataset:
       result = mask.anonymize(text)

CLI Examples
------------

Basic Commands
~~~~~~~~~~~~~~

.. code-block:: bash

   # Initialize config
   cloudmask init-config

   # Anonymize file
   cloudmask anonymize -i input.txt -o output.txt -m mapping.json

   # Anonymize with custom config
   cloudmask anonymize -i input.txt -o output.txt -m mapping.json -c custom.yaml

   # Unanonymize
   cloudmask unanonymize -i anonymized.txt -o original.txt -m mapping.json

Clipboard Operations
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Anonymize clipboard
   cloudmask anonymize --clipboard -m mapping.json

   # Unanonymize clipboard
   cloudmask unanonymize --clipboard -m mapping.json

Custom Configuration
--------------------

YAML Configuration
~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # cloudmask.yaml
   company_names:
     - Acme Corp
     - Example Inc
     - MyCompany LLC

   custom_patterns:
     - pattern: '\bTICKET-\d{4,6}\b'
       name: ticket
     - pattern: '\bPROJ-[A-Z0-9]+'
       name: project

   preserve_prefixes: true
   anonymize_ips: true
   anonymize_domains: false
   seed: my-secret-seed

Loading Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from cloudmask import Config, CloudMask
   from pathlib import Path

   config = Config.from_yaml(Path("cloudmask.yaml"))
   mask = CloudMask(config=config)

Use Cases
---------

LLM Assistance
~~~~~~~~~~~~~~

.. code-block:: python

   from cloudmask import CloudMask

   mask = CloudMask(seed="llm-seed")

   # Anonymize infrastructure code
   terraform_code = Path("main.tf").read_text()
   anonymized = mask.anonymize(terraform_code)

   # Share with LLM
   # ... get response from LLM ...

   # Restore original IDs
   from cloudmask import CloudUnmask
   unmask = CloudUnmask(mapping=mask.mapping)
   restored = unmask.unanonymize(llm_response)

Data Sharing
~~~~~~~~~~~~

.. code-block:: python

   from cloudmask import CloudMask

   mask = CloudMask(seed="sharing-seed")

   # Anonymize diagram
   diagram = """
   [VPC vpc-123]
     [Subnet subnet-456]
       [Instance i-789]
   """

   anonymized = mask.anonymize(diagram)
   mask.save_mapping("private-mapping.json")

   # Share anonymized diagram publicly
   # Keep mapping.json private

Best Practices
--------------

1. **Use Strong Seeds**: Choose unique, random seeds for different projects
2. **Secure Mappings**: Store mapping files separately from anonymized data
3. **Encrypt Sensitive Mappings**: Use encrypted mappings for production data
4. **Version Control**: Never commit mapping files to version control
5. **Batch Processing**: Reuse CloudMask instances for multiple operations
6. **Configuration Management**: Use YAML configs for complex setups
