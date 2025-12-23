API Reference
=============

Core Library
------------

.. automodule:: eml2pdf.libeml2pdf
   :members:
   :undoc-members:
   :show-inheritance:

Data Classes
~~~~~~~~~~~~

.. autoclass:: eml2pdf.libeml2pdf.Attachment
   :members:
   :undoc-members:

.. autoclass:: eml2pdf.libeml2pdf.Email
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: eml2pdf.libeml2pdf.Header
   :members:
   :undoc-members:
   :show-inheritance:

Functions
~~~~~~~~~

.. autofunction:: eml2pdf.libeml2pdf.header_to_html
.. autofunction:: eml2pdf.libeml2pdf.embed_imgs
.. autofunction:: eml2pdf.libeml2pdf.decode_to_str
.. autofunction:: eml2pdf.libeml2pdf.walk_eml
.. autofunction:: eml2pdf.libeml2pdf.get_output_base_path
.. autofunction:: eml2pdf.libeml2pdf.get_exclusive_outfile
.. autofunction:: eml2pdf.libeml2pdf.generate_pdf
.. autofunction:: eml2pdf.libeml2pdf.generate_attachment_list
.. autofunction:: eml2pdf.libeml2pdf.process_eml
.. autofunction:: eml2pdf.libeml2pdf.process_all_emls

Security Module
---------------

.. automodule:: eml2pdf.security
   :members:
   :undoc-members:
   :show-inheritance:

.. autofunction:: eml2pdf.security.sanitize_html
