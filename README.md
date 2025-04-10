# meteodata-lab

A model data processing framework based on xarray.

**DISCLAIMER**

> [!WARNING]
> This project is BETA and will be experimental for the forseable future. Interfaces and functionality are likely to change, and the project itself may be scrapped. Do not use this software in any project/software that is operational.

## Installation


### For Users

To install the latest release from PyPI:

```bash
pip install meteodata-lab
```
#### Optional Extras
To install optional extras:
```bash
pip install "meteodata-lab[polytope,regrid]"
```
**Note**: The `fdb` extra is currently disabled because its dependency `pyfdb` is not available on PyPI. As an alternative the development setup can be used.

### For Development
To set up the project for local development, clone the repository and use the provided Poetry setup script:
```bash
git clone git@github.com:MeteoSwiss/meteodata-lab.git
cd meteodata-lab
./scripts/setup-poetry.sh
```
This will install Poetry (if not already available), set up the virtual environment, and install all dependencies with extras.
