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

SEARCH_URL = "https://sys-data.int.bgdi.ch/api/stac/v1/search"

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
    if asset_url.startswith("https://sys-data.int.bgdi.ch"):
        asset_url = asset_url[29:]

    return asset_url

def get_collection_asset_url(collection_id: str, asset_id:str) -> str:
    """Get collection asset URL from OGD.

    Query the STAC collection assets and return the URL for the given asset ID.

    Parameters
    ----------
    collection_id : str
        Full STAC collection ID, e.g., 'ch.meteoschweiz.ogd-forecasting-icon-ch1'.
    asset_id : str
        The ID of the static asset to retrieve, e.g., 'horizontal_constants_icon-ch1-eps.grib2'.

    Returns
    -------
    str
        The pre-signed URL of the requested static asset.

    Raises
    ------
    ValueError
        If the asset is not found in the collection.
    """
    url = f"{SEARCH_URL}/{collection_id}/assets"

    response = session.get(url)
    response.raise_for_status()

    assets = response.json().get("assets", {})
    asset_info = assets.get(asset_id)

    if not asset_info or "href" not in asset_info:
        raise ValueError(f"Asset '{asset_id}' not found in collection '{collection_id}'.")

    return asset_info["href"]


def _get_geo_coord_url(uuid: UUID) -> str:
    if (var := os.environ.get("MDL_GEO_COORD_URL")) is not None:
        return var

    model_name = icon_grid.GRID_UUID_TO_MODEL.get(uuid)
    if model_name is None:
        raise KeyError("Grid UUID not found")

    base_model = model_name.removesuffix("-eps")
    collection_id = f"ch.meteoschweiz.ogd-forecasting-{base_model}"
    asset_id = f"horizontal_constants_{model_name}.grib2"

    return get_collection_asset_url(collection_id, asset_id)


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
    """Download forecast asset and its static coordinate files from OGD.

    The request attributes define filters for the STAC search API according
    to the forecast extension.

    In addition to the main asset, this function downloads static files
    with horizontal and vertical coordinates, as the forecast item
    contain no height, longitude, or latitude information.

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
    # Download main forecast asset
    asset_url = get_asset_url(request)
    _download_with_checksum(asset_url, target)

    model_suffix = request.collection.value.removeprefix("ogd-forecasting-")
    collection_id = f"ch.meteoschweiz.{request.collection.value}"

    # Download coordinate files
    for prefix in ["horizontal", "vertical"]:
        asset_id = f"{prefix}_constants_icon-{model_suffix}-eps.grib2"
        url = get_collection_asset_url(collection_id, asset_id)
        _download_with_checksum(url, target)


def _download_with_checksum(url: str, target: Path) -> None:
    response = session.get(url, stream=True)
    response.raise_for_status()

    filename = Path(urlparse(url).path).name
    path = target / filename if target.is_dir() else target

    if path.exists():
        logger.info(f"File already exists, skipping download: {path}")
        return

    hasher = hashlib.sha256()
    with path.open("wb") as f:
        for chunk in response.iter_content(16 * 1024):
            f.write(chunk)
            hasher.update(chunk)

    hash = response.headers.get("X-Amz-Meta-Sha256")
    if hash is not None and hash != hasher.hexdigest():
        raise RuntimeError(f"Checksum verification failed for {filename}")
