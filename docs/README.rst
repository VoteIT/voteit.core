Building and changing the docs
==============================

.. todo:: FIXME proper explanation

Some notes on building the docs, commands from the buldout root.

.. code-block:: bash

   source bin/activate
   cd src/voteit.core
   pip install -r requirements.txt
   python setup.py develop
   cd docs
   make html

To pull things in _api with sphinx-apidoc i used the following command.

.. code-block:: bash

   sphinx-apidoc -ET -d 1 -o _api ../voteit/core/

This needs cleanup, apidoc doesn't seem to be finished. It incldues tests, and has no option to ignore them :/
