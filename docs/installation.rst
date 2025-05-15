.. highlight:: shell

============
Installation
============

For Users
=========

To install the latest release from PyPI:

.. code-block:: bash

   pip install meteodata-lab

Optional Extras
---------------

To install optional extras:

.. code-block:: bash

   pip install "meteodata-lab[polytope,regrid]"

.. note::

   The ``fdb`` extra is currently disabled because its dependency ``pyfdb`` is not available on PyPI. As an alternative, the development setup can be used.

For Contributors
================

To set up the project for local development (e.g. for contributing code or testing changes), follow these steps:

1. If you don't have write access, first fork the repository on GitHub, then clone your fork:

   .. code-block:: bash

      git clone git@github.com:your-username/meteodata-lab.git

   If you do have write access, you can clone the main repository directly:

   .. code-block:: bash

      git clone git@github.com:MeteoSwiss/meteodata-lab.git

2. Navigate to the project directory and run the setup script:

   .. code-block:: bash

      cd meteodata-lab
      ./scripts/setup_poetry.sh

   This will install Poetry (if not already available), set up the virtual environment, and install all dependencies with extras.


Interaction with Jenkins and Github actions
-------------------------------------------

Your package is always built on a Github actions server upon committing to the main branch. If your code goes into production, pinned production installations must be tested with Jenkins on CSCS machines. Templates may be found in the jenkins/ folder. Contact DevOps to help you set up your pipeline.
