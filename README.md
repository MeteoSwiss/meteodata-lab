# meteodata-lab
<!-- To update when it's released -->
[![PyPI version](https://img.shields.io/pypi/v/your-package-name.svg)](https://pypi.org/project/your-package-name/)

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
### For Development
To set up the project for local development, clone the repository and use the provided Poetry setup script:
```bash
git clone git@github.com:MeteoSwiss/meteodata-lab.git
cd meteodata-lab
./scripts/setup_poetry.sh
```
This will install Poetry (if not already available), set up the virtual environment, and install all dependencies with extras.
