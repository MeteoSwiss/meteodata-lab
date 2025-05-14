Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit helps, and credit will always be given.

Types of Contributions
----------------------

You can contribute in many ways.

Report Bugs
~~~~~~~~~~~

Report bugs as `GitHub issues <https://github.com/MeteoSwiss/meteodata-lab/issues>`_.

If you are reporting a bug, please include

- your operating system name and version,
- any details about your local setup that might be helpful in troubleshooting, and
- detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the `GitHub issues <https://github.com/MeteoSwiss/meteodata-lab/issues>`_ for bugs. Anything tagged with "bug" and "help wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the `GitHub issues <https://github.com/MeteoSwiss/meteodata-lab/issues>`_ for features. Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

meteodata-lab could always use more documentation, whether as part of the official meteodata-lab docs, in docstrings --- or even on the web in blog posts, articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file a `GitHub issues <https://github.com/MeteoSwiss/meteodata-lab/issues>`_.

If you are proposing a feature,

- explain in detail how it would work;
- keep the scope as narrow as possible, to make it easier to implement; and
- remember that this is a volunteer-driven project, and that contributions are welcome! :)

Get Started!
------------

Ready to contribute? Here's how to set up ``meteodata-lab`` for local development.

1. Fork the `meteodata-lab repo <https://github.com/MeteoSwiss/meteodata-lab>`_ on GitHub.

2. Clone your fork locally:

   .. code-block:: bash

      git clone git@github.com:your-username/meteodata-lab.git

3. Create a virtual environment and install the dependencies:

   .. code-block:: bash

      cd meteodata-lab/
      scripts/setup_poetry.sh

   This will install poetry and create a virtual environment under the ``.venv`` path and install all dependencies including the development group and extras.
   The dependency versions are defined in the ``poetry.lock`` file. The ``meteodata-lab`` package is installed into the virtual environment in editable mode.

   To update the dependency versions, run ``poetry update``. This command will regenerate the lock file which can be committed along with the code changes.

4. Create a branch for local development:

   .. code-block:: bash

      git switch -c name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done with a change, format and check the code using various installed tools like ``black``, ``isort``, ``mypy``, ``flake8`` or ``pylint``. Those that are set up as pre-commit hooks can be run together with:

   .. code-block:: bash

      pre-commit run -a

   Next, ensure that the code does what it is supposed to do by running the tests with pytest:

   .. code-block:: bash

      pytest -m "not ifs"
      pytest -m ifs

   Note that, currently, test data can only be found on balfrin.

6. Commit your changes and push your branch to GitHub:

   .. code-block:: bash

      git add .
      git commit -m "fixed this and did that"
      git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put your new functionality into a function with a docstring, and add the feature to the list in ``README.md``.

Versioning
----------

In order to release a new version of your project, follow these steps:

- Make sure everything is committed, cleaned up and validating (duh!). Don't forget to keep track of the changes in ``HISTORY.md``.
- Increase the version number that is hardcoded in ``pyproject.toml`` (and only there) and commit.

How to provide executable scripts
---------------------------------

By default, a single executable script called meteodata-lab is provided. It is created when the package is installed. When you call it, the main function (``cli``) in ``src/meteodatalab/cli.py`` is called.

When the package is installed, a executable script named ``meteodata-lab`` is created in the bin folder of the active conda environment. Upon calling this script in the shell, the ``main`` function in ``src/meteodatalab/cli.py`` is executed.

The scripts, their names and entry points are specified in ``pyproject.toml`` in the ``[tool.poetry.scripts]`` section. Just add additional entries to provide more scripts to the users of your package.

Release Process
---------------

Perform the following steps to publish a new version of the python package:

* Create a branch named ``rel-v<version>``.
* Ensure that the ``HISTORY.md`` contains all relevant changes and add a new section for the version to be released.
* Update the version string:

  * Remove pre-release flags.
  * Ensure that the changes are compliant with SemVer.
* Request a code review on the branch and merge it to ``main``.
* Create and push a tag ``v<version>``.
