Architecture
============

Overview
--------

CloudMask is designed with a modular architecture that separates concerns and provides flexibility for different use cases.

Components
----------

Core Module (core.py)
~~~~~~~~~~~~~~~~~~~~~

The core module contains the main anonymization logic:

* **CloudMask**: Main class for anonymizing text and files
* **CloudUnmask**: Class for reversing anonymization
* **Config**: Configuration management
* **Pattern Matching**: AWS resource ID detection and replacement

Key Features:

* Hash-based deterministic anonymization
* Prefix preservation for AWS resource IDs
* Custom pattern support via regex
* File and text processing

Security Module (security.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Handles encryption and secure storage of mapping files:

* **Encryption**: AES-256 encryption using Fernet
* **Key Derivation**: PBKDF2 with SHA256
* **Secure Storage**: Encrypted mapping file format

Rate Limiting Module (ratelimit.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides rate limiting for batch operations:

* **RateLimiter**: Token bucket algorithm
* **BatchRateLimiter**: Batch operation tracking
* **Thread-safe**: Uses threading locks

CLI Module (cli.py)
~~~~~~~~~~~~~~~~~~~

Command-line interface:

* **argparse-based**: Standard Python CLI
* **Subcommands**: anonymize, unanonymize, init-config
* **Clipboard support**: Direct clipboard operations

Data Flow
---------

Anonymization Flow
~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Input Text
      ↓
   Pattern Detection (AWS IDs, IPs, etc.)
      ↓
   Hash Generation (SHA256 + seed)
      ↓
   Prefix Preservation (vpc-, i-, etc.)
      ↓
   Mapping Storage
      ↓
   Anonymized Output

Unanonymization Flow
~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Anonymized Text
      ↓
   Load Mapping
      ↓
   Pattern Detection
      ↓
   Mapping Lookup
      ↓
   Replacement
      ↓
   Original Text

Design Patterns
---------------

Builder Pattern
~~~~~~~~~~~~~~~

The ``Config`` class uses a builder-like pattern for configuration:

.. code-block:: python

   config = Config(
       company_names=["Acme"],
       preserve_prefixes=True,
       anonymize_ips=True
   )

Context Manager
~~~~~~~~~~~~~~~

``TemporaryMask`` provides automatic cleanup:

.. code-block:: python

   with TemporaryMask(seed="temp") as mask:
       result = mask.anonymize(text)
   # Mapping automatically discarded

Strategy Pattern
~~~~~~~~~~~~~~~~

Different anonymization strategies for different resource types:

* AWS Resource IDs: Prefix-preserving hash
* Account IDs: Full hash
* IP Addresses: Structured hash
* Custom Patterns: Configurable replacement

Hash Algorithm
--------------

Deterministic Hashing
~~~~~~~~~~~~~~~~~~~~~

CloudMask uses SHA256 with a seed for deterministic anonymization:

.. code-block:: python

   hash_input = f"{seed}:{original_value}"
   hash_output = hashlib.sha256(hash_input.encode()).hexdigest()
   anonymized = prefix + hash_output[:length]

Benefits:

* Same input always produces same output (with same seed)
* Cryptographically secure
* Collision-resistant
* Fast computation

Prefix Preservation
~~~~~~~~~~~~~~~~~~~

AWS resource IDs maintain their prefixes:

* ``vpc-123abc`` → ``vpc-a1b2c3``
* ``i-456def`` → ``i-d4e5f6``
* ``sg-789ghi`` → ``sg-g7h8i9``

This preserves:

* Resource type information
* AWS CLI compatibility
* Human readability

Security Considerations
-----------------------

Seed Security
~~~~~~~~~~~~~

The seed is critical for security:

* Use strong, random seeds
* Different seeds for different projects
* Never share seeds with anonymized data
* Store seeds securely (environment variables, secrets manager)

Mapping Security
~~~~~~~~~~~~~~~~

Mapping files contain reversible information:

* Store separately from anonymized data
* Use encryption for sensitive mappings
* Implement access controls
* Regular rotation for long-term use

Hash Strength
~~~~~~~~~~~~~

SHA256 provides:

* 256-bit security
* Collision resistance
* Pre-image resistance
* Second pre-image resistance

Performance
-----------

Time Complexity
~~~~~~~~~~~~~~~

* Pattern matching: O(n) where n is text length
* Hash generation: O(1) per match
* Overall: O(n × m) where m is average matches per character

Space Complexity
~~~~~~~~~~~~~~~~

* Mapping storage: O(k) where k is unique values
* Memory usage: O(n) for text processing
* Streaming support: O(1) for large files (future)

Optimization Strategies
~~~~~~~~~~~~~~~~~~~~~~~

1. **Compiled Regex**: Pre-compile patterns
2. **Caching**: Reuse hash computations
3. **Batch Processing**: Amortize overhead
4. **Lazy Loading**: Load mappings on demand

Extensibility
-------------

Custom Patterns
~~~~~~~~~~~~~~~

Add new pattern types via configuration:

.. code-block:: yaml

   custom_patterns:
     - pattern: '\bCUSTOM-\d+'
       name: custom_id

Plugin Architecture (Future)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Planned support for:

* Custom anonymizers
* Custom hash algorithms
* Custom storage backends
* Custom validators

Testing Strategy
----------------

Unit Tests
~~~~~~~~~~

* Core functionality
* Edge cases
* Error handling
* Security features

Integration Tests
~~~~~~~~~~~~~~~~~

* CLI commands
* File operations
* Configuration loading
* End-to-end workflows

Performance Tests
~~~~~~~~~~~~~~~~~

* Large file processing
* Batch operations
* Memory usage
* Rate limiting

Security Tests
~~~~~~~~~~~~~~

* Encryption/decryption
* Hash collision resistance
* Input validation
* Injection prevention
