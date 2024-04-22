# meteodata-lab: Prototype for a model data processing framework on the basis of xarray.

## Install

Once you created or cloned this repository, make sure the installation is running properly. Install the package dependencies with the provided script `setup_env.sh`.
Check available options with
```bash
tools/setup_env.sh -h
```
We distinguish pinned installations based on exported (reproducible) environments and free installations where the installation
is based on top-level dependencies listed in `requirements/requirements.yaml`. If you start developing, you might want to do an unpinned installation and export the environment:

```bash
tools/setup_env.sh -u -e -n <package_env_name>
```
*Hint*: If you are the package administrator, it is a good idea to understand what this script does, you can do everything manually with `conda` instructions.

*Hint*: Use the flag `-m` to speed up the installation using mamba. Of course you will have to install mamba first (we recommend to install mamba into your base
environment `conda install -c conda-forge mamba`. If you install mamba in another (maybe dedicated) environment, environments installed with mamba will be located
in `<miniconda_root_dir>/envs/mamba/envs`, which is not very practical.

The package itself is installed with `pip`. For development, install in editable mode:

```bash
conda activate <package_env_name>
pip install --editable .
```

*Warning:* Make sure you use the right pip, i.e. the one from the installed conda environment (`which pip` should point to something like `path/to/miniconda/envs/<package_env_name>/bin/pip`).

Once your package is installed, run the tests by typing:

```
conda activate <package_env_name>
pytest
```

If the tests pass, you are good to go. If not, contact the package administrator Tobias Wicky. Make sure to update your requirement files and export your environments after installation
every time you add new imports while developing. Check the next section to find some guidance on the development process if you are new to Python and/or APN.

## Credits

This package was created with [`copier`](https://github.com/copier-org/copier) and the [`MeteoSwiss-APN/mch-python-blueprint`](https://meteoswiss-apn.github.io/mch-python-blueprint/) project template.
