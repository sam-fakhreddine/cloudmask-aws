Getting Started
===============

Installation
------------

CloudMask requires Python 3.10 or higher.

Using pip
~~~~~~~~~

.. code-block:: bash

   pip install cloudmask

Using uv
~~~~~~~~

.. code-block:: bash

   uv pip install cloudmask

From Source
~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/yourusername/cloudmask.git
   cd cloudmask
   uv pip install -e ".[dev]"

Requirements
------------

* Python 3.10+
* PyYAML 6.0+
* pyperclip 1.11+
* cryptography 41.0+

Quick Start
-----------

CLI Usage
~~~~~~~~~

Generate a configuration file:

.. code-block:: bash

   cloudmask init-config

Anonymize a file:

.. code-block:: bash

   cloudmask anonymize -i infrastructure.txt -o anonymized.txt -m mapping.json

Anonymize clipboard content:

.. code-block:: bash

   cloudmask anonymize --clipboard -m mapping.json

Restore original values:

.. code-block:: bash

   cloudmask unanonymize -i llm-response.txt -o restored.txt -m mapping.json

Python Library
~~~~~~~~~~~~~~

.. code-block:: python

   from cloudmask import CloudMask, CloudUnmask

   # Anonymize text
   mask = CloudMask(seed="my-secret-seed")
   anonymized = mask.anonymize("""
       Instance i-1234567890abcdef0 is running in vpc-abcdef123456
       Account: 123456789012
   """)

   # Save mapping
   mask.save_mapping("mapping.json")

   # Unanonymize later
   unmask = CloudUnmask(mapping_file="mapping.json")
   original = unmask.unanonymize(anonymized)

Configuration
-------------

Create a ``cloudmask.yaml`` file:

.. code-block:: yaml

   company_names:
     - Acme Corp
     - Example Inc

   custom_patterns:
     - pattern: '\bTICKET-\d{4,6}\b'
       name: ticket

   preserve_prefixes: true
   anonymize_ips: true
   seed: my-secret-seed

Next Steps
----------

* Read the :doc:`usage` guide for detailed examples
* Explore the :doc:`api` reference
* Review :doc:`security` considerations
