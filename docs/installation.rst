.. highlight:: shell

============
Installation
============

There are two installation types, a production installation, which is static, and a development installation, which is editable.


Preparation
-----------

To install Icon Data Processing Incubator you need a miniconda installation. You can either set up your miniconda installation manually or use the script `tools/setup_miniconda.sh`, which will download and install the latest version of miniconda.


Installation of dependencies
----------------------------

Dependencies are handled by the conda package manager. The goal of this step is to set up a conda environment according to the requirements of Icon Data Processing Incubator. Note that by design, there are some dependencies already when you start developing the package, as the environment includes linters and other development tools.

The dependencies are handled in requirement files. Free installations are based on the `requirements/requirements.yaml` file, where the top-level dependencies of the package are listed. Pinned installations are based on exported environments and stored in the file `requirements/environment.yaml`.

Environments (based on either unpinned or pinned requirements) are handled by the script `tools/setup_env.sh`. The optional flag `-u` stands for unpinned installation:

.. code-block:: console

    $ bash tools/setup_env.sh -u

This will create an up-to-date environment that can be exported to `requirements/environment.yaml` with the optional flag `-e` (see below).

You can control the environment name with the flag `-n` and the Python version with `-v`. Run :code:`./tools/setup_env -h` for available options and defaults (incl. mamba support).


Installation of Icon Data Processing Incubator
-----------------------------------------------

After creating and activating your environment by running

.. code-block:: console

    $ ./tools/setup_env.sh
    $ conda activate icon-data-processing-incubator

in the root folder of icon-data-processing-incubator, type

.. code-block:: console

    $ python -m pip install --no-deps .

for a (static) production installation and

.. code-block:: console

    $ pip install --no-deps --editable .

for a (editable) development installation.


Maintenance of the environment (for developers)
-----------------------------------------------

If you need to add new first-level dependencies to your package, make sure to include them in `requirements/requirements.yaml`. (Note that pip requirements can be added to these files in the `- pip:` section of the document.) After a (unpinned!) installation, this will change the full dependency tree and you need to export the environment. You can either do this by hand by activating the environment and then running

.. code-block:: console

    $ conda env export icon-data-processing-incubator requirements/environment.yaml

or you can reinstall with the setup script from `requirements/requirements.yaml` and directly export the environment with the `-e` flag.

.. code-block:: console

    $ ./tools/setup_env -ue


Interaction with Jenkins and Github actions
-------------------------------------------

Your package is always built on a Github actions server upon committing to the main branch. If your code goes into production, pinned production installations must be tested with Jenkins on CSCS machines. Templates may be found in the jenkins/ folder. Contact DevOps to help you set up your pipeline.
