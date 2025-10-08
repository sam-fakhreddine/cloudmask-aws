CloudMask Documentation
=======================

**Anonymize AWS infrastructure identifiers for secure LLM processing**

CloudMask helps you safely share AWS infrastructure data with Large Language Models by anonymizing sensitive identifiers while maintaining structure and reversibility.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   usage
   api
   architecture
   security
   troubleshooting
   migration

Features
--------

* 🔒 **Secure Anonymization**: Hash-based deterministic anonymization
* 🔄 **Reversible**: Complete mapping for unanonymization
* 🏗️ **Structure-Preserving**: Maintains AWS resource ID prefixes (vpc-, i-, etc.)
* ⚙️ **Configurable**: YAML-based configuration for company names and custom patterns
* 🐍 **Dual Interface**: Use as CLI tool or Python library

Quick Example
-------------

.. code-block:: python

   from cloudmask import anonymize, unanonymize

   # Anonymize text
   text, mapping = anonymize(
       "Instance i-123 in account 123456789012",
       seed="my-seed"
   )

   # Restore original
   original = unanonymize(text, mapping)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
