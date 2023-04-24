# Contributing

Contributions are welcome, and they are greatly appreciated! Every little bit helps, and credit will always be given.

## Types of Contributions

You can contribute in many ways.

### Report Bugs

Report bugs as [GitHub issues](https://github.com/MeteoSwiss-APN/icon-data-processing-incubator/issues).

If you are reporting a bug, please include

- your operating system name and version,
- any details about your local setup that might be helpful in troubleshooting, and
- detailed steps to reproduce the bug.

### Fix Bugs

Look through the [GitHub issues](https://github.com/MeteoSwiss-APN/icon-data-processing-incubator/issues) for bugs. Anything tagged with "bug" and "help wanted" is open to whoever wants to implement it.

### Implement Features

Look through the  [GitHub issues](https://github.com/MeteoSwiss-APN/icon-data-processing-incubator/issues) for features. Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

### Write Documentation

Icon Data Processing Incubator could always use more documentation, whether as part of the official Icon Data Processing Incubator docs, in docstrings --- or even on the web in blog posts, articles, and such.

### Submit Feedback

The best way to send feedback is to file a [GitHub issue]( https://github.com/MeteoSwiss-APN/icon-data-processing-incubator/issues).

If you are proposing a feature,

- explain in detail how it would work;
- keep the scope as narrow as possible, to make it easier to implement; and
- remember that this is a volunteer-driven project, and that contributions are welcome! :)

## Get Started!

Ready to contribute? Here's how to set up `icon-data-processing-incubator` for local development.

1. Fork the [`icon-data-processing-incubator` repo](https://github.com/) on GitHub.
2. Clone your fork locally:

    ```bash
    git clone git@github.com:your_name_here/icon-data-processing-incubator.git
    ```

3. Create a virtual environment and install the dependencies:

    ```bash
    cd icon-data-processing-incubator/
    ./tools/setup_env.sh
    ```

    This will create a conda environment named `icon-data-processing-incubator` (change with `-n`) and install the pinned runtime and development dependencies in `requirements/environment.yaml`.

    Install the package itself in editable mode.

    ```bash
    conda activate icon-data-processing-incubator
    pip install --editable .
    ```

    Use `-u` to get the newest package versions (unpinned dependencies in `requirements/requirements.yaml`), and additionally `-e` to update the environment files.

4. Create a branch for local development:

    ```bash
    git switch -c name-of-your-bugfix-or-feature
    ```

    Now you can make your changes locally.

5. When you're done with a change, format and check the code using various installed tools like `black`, `isort`, `mypy`, `flake8` or `pylint`. Those that are set up as pre-commit hooks can be run together with:

    ```bash
    pre-commit run -a
    ```

    Next, ensure that the code does what it is supposed to do by running the tests with pytest:

    ```bash
    pytest
    ```

6. Commit your changes and push your branch to GitHub:

    ```bash
    git add .
    git commit -m "fixed this and did that"
    git push origin name-of-your-bugfix-or-feature
    ```

7. Submit a pull request through the GitHub website.

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put your new functionality into a function with a docstring, and add the feature to the list in `README.md`.
3. The pull request should work for Python 3.6 and 3.7, and for PyPy. Make sure that the tests pass for all supported Python versions.

## Tips

For a subset of tests or a specific test, run:

```bash
pytest tests.test_idpi
pytest tests.test_idpi/test_feature::test_edge_case
```

## Versioning

In order to release a new version of your project, follow these steps:

- Make sure everything is committed, cleaned up and validating (duh!). Don't forget to keep track of the changes in `HISTORY.md`.
- Increase the version number that is hardcoded in `pyproject.toml` (and only there) and commit.
- Either create a (preferentially annotated) tag with `git tag`, or directly create a release on GitHub.

## Project Structure

Following is a description of the most important files and folders in the project in alphabetic order.

- `.github/workflows/`: [GitHub Actions](https://docs.github.com/en/actions) workflows, e.g., checks that are run when certain branches are pushed.
- `docs/`: Documentation.
- `jenkins/`: Jenkins setup.
- `requirements/`: Project dependencies and environment
    - `environment.yaml`: Full tree of runtime and development dependencies with fully specified ('pinned') version numbers; created with `conda env export`.
    - `requirements.yaml`: Top-level runtime and development dependencies with minimal version restrictions (typically a minimum version or a version range); kept manually.
- `src/idpi/`: Source code of the project package.
- `tests/test_idpi/`: Unit tests of the project package; run with `pytest`.
- `tools/`: Scripts primarily for development
    - `run-mypy.sh`: Run script for the static type checker `mypy`.
    - `setup_env.sh`: Script to create new conda environments; see `tools/setup_env.sh -h` for all available options.
    - `setup_miniconda.sh`: Script to install miniconda.
- `.gitignore`: Files and folders ignored by `git`.
- `.pre-commit-config.yaml`: Configuration of pre-commit hooks, which are formatters and checkers run before a successful commit.
- `AUTHORS.md`: Project authors.
- `CONTRIBUTING.md`: Instructions on how to contribute to the project.
- `HISTORY.md`: List of changes for each version of the project.
- `LICENSE`: License of the project.
- `MANIFEST.in`: Files installed alongside the source code.
- `pyproject.toml`: Main package specification file, including build dependencies, metadata and the configurations of development tools like `black`, `pytest`, `mypy` etc.
- `README.md`: Description of the project.
- `USAGE.md`: Information on how to use the package.

## Managing dependencies

Icon Data Processing Incubator uses [Conda](https://docs.conda.io/en/latest/) to manage dependencies. (Also check out [Mamba](https://mamba.readthedocs.io/en/latest/) if you like your package installations fast.) Dependencies are specified in YAML files, of which there are two:

- `requirements/requirements.yaml`: Top-level runtime and development dependencies with minimal version restrictions (typically a minimum version or a version range); kept manually.
- `requirements/environment.yaml`: Full tree of runtime and development dependencies with fully specified ('pinned') version numbers; created with `conda env export`.

The pinned `environment.yaml` file should be used to create reproducible environments for development or deployment. This ensures reproducible results across machines and users. The unpinned `requirements.yaml` file has two main purposes: (i) keeping track of the top-level dependencies, and (ii) periodically updating the pinned `environment.yaml` file to the latest package versions.

After introducing new first-level dependencies to your requirements, you have to update the environment files in order to be able to create reproducible environments for deployment and production.
Updating the environment files involves the following steps:

1. Creating an environment from your top-level dependencies in `requirements/requirements.yaml`
2. Exporting this environment to `requirements/environment.yaml`

Alternatively, use the provided script

```bash
./tools/setup_env.sh -ue
```

to create a environment from unpinned (`-u`) runtime and development dependencies and export (`-e`) it (consider throwing in `-m` for good measure to speed things up with `mamba`).

_Note that the separation of unpinned runtime and development dependencies into separate files (`requirements.yaml` and `dev-requirements.yaml`, respectively) has been given up because when creating an environment from multiple YAML files (with `conda env create` and `conda env update`), only the version restrictions in the last file are guaranteed to be respected, so when installing devevelopment dependencies from `dev-requirements.yaml` into an environment created from `requirements.yaml`, the solver does not take version restrictions in the latter file into account anymore, potentially resulting in inconsistent production and development environments. Given the negligible overhead (in terms of memory etc.) of installing development dependencies in production environments, they are only separated from the runtime dependencies in `requirements.yaml` by a comment._

## How to provide executable scripts

By default, a single executable script called icon-data-processing-incubator is provided. It is created when the package is installed. When you call it, the main function (`cli`) in `src/idpi/cli.py` is called.

When the package is installed, a executable script named `icon-data-processing-incubator` is created in the bin folder of the active conda environment. Upon calling this script in the shell, the `main` function in `src/idpi/cli.py` is executed.

The scripts, their names and entry points are specified in `pyproject.toml` in the `[project.scripts]` section. Just add additional entries to provide more scripts to the users of your package.
