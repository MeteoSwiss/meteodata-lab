# meteodata-lab

<p align="center">
    <picture>
        <img src="https://raw.githubusercontent.com/MeteoSwiss/meteodata-lab/main/docs/assets/meteodata-lab_logo.gif"
            style="max-height: 200px; height: auto; width: auto;"
            alt="Animated logo">
    </picture>
</p>
<p align="center">
    <a href="https://pypi.org/project/meteodata-lab/">
    <img src="https://img.shields.io/pypi/v/meteodata-lab.svg?color=ff69b4" alt="PyPI version">
    </a>
    <a href="https://github.com/meteoswiss/meteodata-lab/releases">
    <img src="https://img.shields.io/github/v/release/meteoswiss/meteodata-lab?color=purple&label=Release" alt="Latest Release">
    </a>
    <a href="https://opensource.org/licenses/mit">
    <img src="https://img.shields.io/badge/licence-MIT-blue.svg" alt="Licence">
    </a>
</p>

<p align="center">
    <a href="#installation">Installation</a> •
    <a href="https://meteoswiss.github.io/meteodata-lab/">Documentation</a>
</p>

> **WARNING:**
>
> This project is in BETA and under active development. Interfaces and functionality are subject to change.

**Meteodata-lab** is a NumPy/Xarray-based Python library for processing and analyzing gridded meteorological data. It supports GRIB (read/write) and is tailored to common workflows that require data interpolation, regridding to custom grids (e.g., Swiss grid or rotated lat/lon), and the computation of advanced meteorological fields. One of the key features of meteodata-lab is its use of operators that ensure the integrity of GRIB metadata is maintained throughout processing, allowing for consistent writing back to GRIB format.

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

### For Contributors
To set up the project for local development (e.g. for contributing code or testing changes), follow these steps:
1. If you don't have write access, first fork the repository on GitHub, then clone your fork:
    ```bash
    git clone git@github.com:your-username/meteodata-lab.git
    ```
    If you do have write access, you can clone the main repository directly:
    ```bash
    git clone git@github.com:MeteoSwiss/meteodata-lab.git
    ```
2. Navigate to the project directory and run the setup script:
    ```bash
    cd meteodata-lab
    ./scripts/setup_poetry.sh
    ```
    This will install Poetry (if not already available), set up the virtual environment, and install all dependencies with extras.


You can find more information about contributing to meteodata-lab at our [Contributing page](https://meteoswiss.github.io/meteodata-lab/contributing.html).

## Documentation

Learn more about meteodata-lab in its official documentation at [meteoswiss.github.io/meteodata-lab/](https://meteoswiss.github.io/meteodata-lab/).

Try out [interactive Juypter notebooks](https://github.com/MeteoSwiss/opendata-nwp-demos)
