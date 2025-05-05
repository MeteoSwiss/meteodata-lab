# Usage

## Using `ogd_api` to access ICON-CH1/2-EPS forecasts

The `ogd_api` module allows you to query and retrieve weather forecast data published through data.geo.admin.ch's extended [STAC API](https://data.geo.admin.ch/api/stac/static/spec/v0.9/api.html).

You can find interactive Jupyter notebooks demonstrating the usage of `ogd_api` here: [MeteoSwiss Open Data NWP Demos](https://github.com/MeteoSwiss/opendata-nwp-demos).

This example walks you through creating requests and retrieving forecast data.

### Step 1: Build requests
Use `ogd_api.Request` to define a query, for example, to retrieve ICON-CH2-EPS total precipitation.

```python
from datetime import datetime, timezone
from meteodatalab import ogd_api

today = datetime.now(timezone.utc).replace(hour=0, minute=0)

req = ogd_api.Request(
    collection="ogd-forecasting-icon-ch2",
    variable="TOT_PREC",
    reference_datetime=today,
    perturbed=False,
    horizon=f"P0DT2H"
)
```

Each argument in the request serves the following purpose:

| Argument             | Description |
|----------------------|-------------|
| `collection`         | Forecast collection to use (e.g., `ogd-forecasting-icon-ch1` for ICON-CH1-EPS and `ogd-forecasting-icon-ch2` for ICON-CH2-EPS). |
| `variable`           | Meteorological variable of interest (`TOT_PREC` = total precipitation). |
| `reference_datetime` | Initialization time of the forecast in **UTC**, provided as either:<br>- [datetime.datetime](https://docs.python.org/3/library/datetime.html#datetime-objects) object (e.g.,<br> &nbsp; `datetime.datetime(2025, 5, 22, 9, 0, 0, tzinfo=datetime.timezone.utc)`) <br>- [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601#Combined_date_and_time_representations) date string (e.g., `"2025-05-22T09:00:00Z"`)|
| `perturbed`          | If `True`, retrieves ensemble forecast members; if `False`, returns the deterministic forecast. |
| `horizon`            | Forecast lead time, provided as either:<br>– [datetime.timedelta](https://docs.python.org/3/library/datetime.html#timedelta-objects) object (e.g., `datetime.timedelta(hours=2)`) <br>– [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601#Durations) duration string (e.g., `"P0DT2H"`)|
### Step 2: Retrieve forecast data
To access the forecast data, you have two choices:
1. Load forecast data to Xarray with `get_from_ogd`
2. Download forecast data with `download_from_ogd`


**1. Load forecast data to Xarray**

We now send our request to the API and retrieve the resulting dataset using the `get_from_ogd` function. The response is returned as an `xarray.DataArray`, which is efficient for handling multi-dimensional data.
>  **Tip**: You can use configure caching behaviour in [earthkit-data](https://earthkit-data.readthedocs.io/en/latest/) to avoid re-downloading files:
> - `"off"` (default): no caching — files are always freshly downloaded
> - `"temporary"`: auto-cleared after the session
> - `"user"`: saves to a specific directory across sessions
>See the [earthkit-data caching docs](https://earthkit-data.readthedocs.io/en/latest/examples/cache.html) for details.

```python
# Enable temporary cache
config.set("cache-policy", "temporary")

# Load data as xarray.DataArray
da = ogd_api.get_from_ogd(req)
```

**2. Download forecast data**
```python
from pathlib import Path

# Define the target directory for saving the forecast files
target_dir = Path.cwd() / "forecast_files"

# Download the forecast files
ogd_api.download_from_ogd(req, target_dir)

# List all downloaded files in the target directory
print("\n Downloaded files:")
for file in sorted(target_dir.iterdir()):
    print(f" - {file.name}")
```

After downloading, you should find the following files inside the `forecast_files/` directory:

- `horizontal_constants_icon-ch2-eps.grib2`
- `horizontal_constants_icon-ch2-eps.sha256`
- `icon-ch2-eps-<today's-datetime>-2-tot_prec-ctrl.grib2`
- `icon-ch2-eps-<today's-datetime>-2-tot_prec-ctrl.sha256`
- `vertical_constants_icon-ch2-eps.grib2`
- `vertical_constants_icon-ch2-eps.sha256`


> **Missing grid coordinates**
> Forecast GRIB files like `icon-ch2-eps-*.grib2` do **not** include horizontal or vertical coordinates (longitude, latitude, or height).
> Therefore, the horizontal and vertical constants are provided as separate files to fully describe the forecast grid. This applies when using
> `download_from_ogd`. If you use `get_from_ogd`, the horizontal coordinates are automatically loaded and included as part of the `xarray.DataArray`.

> **Checksum verification**
> During the download, each file’s integrity is verified using a SHA-256 checksum provided via HTTP headers.
> These checksums are saved as `.sha256` files and used to skip re-downloading valid existing files.

> Learn more about the data structure [here](https://opendatadocs.meteoswiss.ch/e-forecast-data/e2-e3-numerical-weather-forecasting-model).
