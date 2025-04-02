"""Open Government Data API helpers."""

# Standard library
import dataclasses as dc
import datetime as dt
import enum
import hashlib
import logging
import os
import typing
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

# Third-party
import earthkit.data as ekd  # type: ignore
import pydantic
import pydantic.dataclasses as pdc
import xarray as xr
import yaml

# Local
from . import data_source, grib_decoder, icon_grid, util

SEARCH_URL = "https://data.geo.admin.ch/api/stac"

logger = logging.getLogger(__name__)
session = util.init_session(logger)


class Collection(str, enum.Enum):
    ICON_CH1 = "ogd-forecasting-icon-ch1"
    ICON_CH2 = "ogd-forecasting-icon-ch2"


def _forecast_prefix(field_name):
    if field_name in {
        "variable",
        "reference_datetime",
        "perturbed",
        "horizon",
    }:
        return f"forecast:{field_name}"
    return field_name


def _parse_datetime(value: str) -> dt.datetime:
    return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")


@pdc.dataclass(
    frozen=True,
    config=pydantic.ConfigDict(
        use_enum_values=True,
        ser_json_timedelta="iso8601",
        alias_generator=pydantic.AliasGenerator(serialization_alias=_forecast_prefix),
    ),
)
class Request:
    collection: Collection = dc.field(metadata=dict(exclude=True))
    variable: str
    reference_datetime: str
    perturbed: bool
    horizon: dt.timedelta

    if typing.TYPE_CHECKING:
        # https://github.com/pydantic/pydantic/issues/10266
        def __init__(self, *args: typing.Any, **kwargs: typing.Any): ...

    @pydantic.computed_field  # type: ignore[misc]
    @property
    def collections(self) -> list[str]:
        return ["ch.meteoschweiz." + str(self.collection)]

    @pydantic.field_validator("reference_datetime", mode="wrap")
    @classmethod
    def valid_reference_datetime(
        cls, input_value: typing.Any, handler: pydantic.ValidatorFunctionWrapHandler
    ) -> str:
        if isinstance(input_value, dt.datetime):
            if input_value.tzinfo is None:
                logger.warn("Converting naive datetime from local time to UTC")
            fmt = "%Y-%m-%dT%H:%M:%SZ"  # Zulu isoformat
            return input_value.astimezone(dt.timezone.utc).strftime(fmt)

        value = handler(input_value)
        parts = value.split("/")
        match parts:
            case [v, ".."] | ["..", v] | [v]:
                # open ended or single value
                _parse_datetime(v)
            case [v1, v2]:
                # range
                d1 = _parse_datetime(v1)
                d2 = _parse_datetime(v2)
                if d2 < d1:
                    raise ValueError("reference_datetime bounds inverted")
            case _:
                raise ValueError(f"Unable to parse reference_datetime: {value}")
        return value

    def dump(self):
        root = pydantic.RootModel(self)
        return root.model_dump(mode="json", by_alias=True)


def _search(url: str, request: Request):
    response = session.post(url, json=request.dump())
    response.raise_for_status()

    obj = response.json()
    result = []
    for item in obj["features"]:
        for asset in item["assets"].values():
            result.append(asset["href"])

    for link in obj["links"]:
        if link["rel"] == "next":
            result.extend(_search(link["href"], request))

    return result


def get_asset_url(request: Request):
    """Get asset URL from OGD.

    The request attributes define filters for the STAC search API according
    to the forecast extension.

    Parameters
    ----------
    request : Request
        Asset search filters, must select a single asset.

    Raises
    ------
    ValueError
        when the request does not select exactly one asset.

    Returns
    -------
    str
        URL of the selected asset.

    """
    result = _search(SEARCH_URL, request)
    [asset_url] = result  # expect only one asset

    # https://meteoswiss.atlassian.net/browse/OG-62
    if asset_url.startswith("https://data.geo.admin.ch/api/stac"):
        asset_url = asset_url[35:]

    return asset_url


def _get_geo_coord_url(uuid: UUID) -> str:
    if (var := os.environ.get("MDL_GEO_COORD_URL")) is not None:
        return var

    model = icon_grid.GRID_UUID_TO_MODEL.get(uuid)

    if model is None:
        raise KeyError("Grid UUID not found")

    config_path = files("meteodatalab.data").joinpath("geo_coords_urls.yaml")
    urls = yaml.safe_load(config_path.open())
    return urls[model]["horizontal"]


def _no_coords(uuid: UUID) -> dict[str, xr.DataArray]:
    return {}


def _geo_coords(uuid: UUID) -> dict[str, xr.DataArray]:
    url = _get_geo_coord_url(uuid)
    source = data_source.URLDataSource(urls=[url])
    ds = grib_decoder.load(source, {"param": ["CLON", "CLAT"]}, geo_coords=_no_coords)
    return {"lon": ds["CLON"].squeeze(), "lat": ds["CLAT"].squeeze()}


def get_from_ogd(request: Request) -> xr.DataArray:
    """Get data from OGD.

    The request attributes define filters for the STAC search API according
    to the forecast extension. It is recommended to enable caching through
    earthkit-data. A warning message is emitted if the cache is disabled.

    Parameters
    ----------
    request : Request
        Asset search filters, must select a single asset.

    Raises
    ------
    ValueError
        when the request does not select exactly one asset.

    Returns
    -------
    xarray.DataArray
        A data array of the selected asset including GRIB metadata and coordinates.

    """
    if ekd.settings.get("cache-policy") == "off":
        doc = "https://earthkit-data.readthedocs.io/en/latest/examples/cache.html"
        logger.warning("Earthkit-data caching is recommended. See: %s", doc)

    asset_url = get_asset_url(request)

    source = data_source.URLDataSource(urls=[asset_url])
    return grib_decoder.load(
        source,
        {"param": request.variable},
        geo_coords=_geo_coords,
    )[request.variable]


def download_from_ogd(request: Request, target: Path) -> None:
    """Download item from OGD.

    The request attributes define filters for the STAC search API according
    to the forecast extension.

    Parameters
    ----------
    request : Request
        Asset search filters, must select a single asset.
    target : Path
        Target path where to save the asset.
        If the path points to an existing directory, the asset will be
        saved under its own name.

    Raises
    ------
    ValueError
        when the request does not select exactly one asset.
    RuntimeError
        if the checksum verification fails.

    """
    asset_url = get_asset_url(request)
    response = session.get(asset_url, stream=True)
    response.raise_for_status()

    if target.is_dir():
        path = target / Path(urlparse(asset_url).path).name
    else:
        path = target

    hasher = hashlib.sha256()
    with path.open("wb") as f:
        for chunk in response.iter_content(16 * 1024):
            f.write(chunk)
            hasher.update(chunk)

    hash = response.headers.get("X-Amz-Meta-Sha256")
    if hash is not None and hash != hasher.hexdigest():
        raise RuntimeError("Checksum verification failed.")
