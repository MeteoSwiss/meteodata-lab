# icon_data_processing_incubator
Prototype for data processing framework

## How to install the conda environment and run the tests
```
conda env create --file environment_dev.yml
conda activate idpi_env

cd idpi/test
source setup.sh
pytest -s
```

## Pre-commit hooks for formatting and linting
```
pre-commit run --all-files
```
