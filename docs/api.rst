API Reference
=============

Core Classes
------------

CloudMask
~~~~~~~~~

.. autoclass:: cloudmask.CloudMask
   :members:
   :undoc-members:
   :show-inheritance:

CloudUnmask
~~~~~~~~~~~

.. autoclass:: cloudmask.CloudUnmask
   :members:
   :undoc-members:
   :show-inheritance:

Configuration
-------------

Config
~~~~~~

.. autoclass:: cloudmask.Config
   :members:
   :undoc-members:
   :show-inheritance:

CustomPattern
~~~~~~~~~~~~~

.. autoclass:: cloudmask.CustomPattern
   :members:
   :undoc-members:
   :show-inheritance:

Convenience Functions
---------------------

anonymize
~~~~~~~~~

.. autofunction:: cloudmask.anonymize

unanonymize
~~~~~~~~~~~

.. autofunction:: cloudmask.unanonymize

anonymize_dict
~~~~~~~~~~~~~~

.. autofunction:: cloudmask.anonymize_dict

create_batch_anonymizer
~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: cloudmask.create_batch_anonymizer

Context Managers
----------------

TemporaryMask
~~~~~~~~~~~~~

.. autoclass:: cloudmask.TemporaryMask
   :members:
   :undoc-members:
   :show-inheritance:

Security
--------

Encryption Functions
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: cloudmask.encrypt_mapping

.. autofunction:: cloudmask.decrypt_mapping

.. autofunction:: cloudmask.save_encrypted_mapping

.. autofunction:: cloudmask.load_encrypted_mapping

Rate Limiting
-------------

RateLimiter
~~~~~~~~~~~

.. autoclass:: cloudmask.RateLimiter
   :members:
   :undoc-members:
   :show-inheritance:

BatchRateLimiter
~~~~~~~~~~~~~~~~

.. autoclass:: cloudmask.BatchRateLimiter
   :members:
   :undoc-members:
   :show-inheritance:

CLI Module
----------

.. automodule:: cloudmask.cli
   :members:
   :undoc-members:
   :show-inheritance:
