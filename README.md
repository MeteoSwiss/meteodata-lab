<p align="center">
  <picture>
    <img src="./docs/images/meteodata_lab_logo_transparent_cropped.png" height="130">
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

> [!WARNING]
> This project is in BETA and under active development. Interfaces and functionality are subject to change.

MeteoData Lab is a NumPy/Xarray-based Python library for processing and analyzing gridded meteorological data. It supports GRIB (read/write) and is tailored to common workflows that require data interpolation, regridding to custom grids (e.g., Swiss grid or rotated lat/lon), and the computation of advanced meteorological fields.

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
./scripts/setup-poetry.sh
```
This will install Poetry (if not already available), set up the virtual environment, and install all dependencies with extras.
