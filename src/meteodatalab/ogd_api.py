"""Open Government Data API helpers."""

# Standard library
import dataclasses as dc
import datetime as dt
import enum
import hashlib
import logging
import os
import re
import typing
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

# Third-party
import earthkit.data as ekd  # type: ignore
import pydantic
import pydantic.dataclasses as pdc
import xarray as xr

# Local
from . import data_source, grib_decoder, icon_grid, util

API_URL = "https://data.geo.admin.ch/api/stac/v1"

logger = logging.getLogger(__name__)
session = util.init_session(logger)


class Collection(str, enum.Enum):
    #: Collection of icon-ch1-eps model outputs
    ICON_CH1 = "ogd-forecasting-icon-ch1"
    #: Collection of icon-ch2-eps model outputs
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
    """Define filters for the STAC Search API.

    Parameters
    ----------
    collection : Collection
        Name of the STAC collection.
    variable : str
        Name of the variable following the DWD convention.
    reference_datetime : str
        Forecast reference datetime in ISO 8601 format.
        Alias: ref_time
    perturbed : bool
        If true, retrieve ensemble forecast members.
        Otherwise, retrieve deterministic (control) forecast.
    horizon : datetime.timedelta or list[datetime.timedelta]
        Lead time of the requested data.
        Can be supplied as string in ISO 8601 format.
        Alias: lead_time

    """

    collection: Collection = dc.field(metadata=dict(exclude=True))
    variable: str
    reference_datetime: str = dc.field(
        metadata=dict(
            validation_alias=pydantic.AliasChoices("reference_datetime", "ref_time")
        )
    )
    perturbed: bool
    horizon: dt.timedelta | list[dt.timedelta] = dc.field(
        metadata=dict(validation_alias=pydantic.AliasChoices("horizon", "lead_time"))
    )

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
        if value == "latest":
            return value
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

    @pydantic.field_serializer("reference_datetime")
    def serialize_reference_datetime(self, value: str):
        if value == "latest":
            cutoff = dt.datetime.now(tz=dt.timezone.utc) - dt.timedelta(hours=48)
            fmt = "%Y-%m-%dT%H:%M:%SZ"  # Zulu isoformat
            return f"{cutoff.strftime(fmt)}/.."
        return value

    def dump(self):
        exclude_fields = {}
        if isinstance(self.horizon, list):
            exclude_fields["horizon"] = True

        root = pydantic.RootModel(self)
        return root.model_dump(mode="json", by_alias=True, exclude=exclude_fields)


def _search(url: str, body: dict | None = None):
    response = session.post(url, json=body)
    response.raise_for_status()

    obj = response.json()
    result = []
    for item in obj["features"]:
        for asset in item["assets"].values():
            result.append(asset["href"])

    for link in obj["links"]:
        if link["rel"] == "next":
            if link["method"] != "POST" or not link["merge"]:
                raise RuntimeError(f"Bad link: {link}")
            result.extend(_search(link["href"], body | link["body"]))

    return result


def get_asset_urls(request: Request) -> list[str]:
    """Get asset URLs from OGD.

    The request attributes define filters for the STAC search API according
    to the forecast extension. Forecasts reference datetimes for which not all
    requested lead times are present are excluded from the result.

    Parameters
    ----------
    request : Request
        Asset search filters

    Raises
    ------
    ValueError
        when no datetime can be found in the asset URL for 'latest' requests.

    Returns
    -------
    list[str]
        URLs of the selected assets.

    """
    result = _search(f"{API_URL}/search", request.dump())

    if len(result) == 1:
        return result

    lead_times = (
        request.horizon if isinstance(request.horizon, list) else [request.horizon]
    )

    pattern = re.compile(r"-(?P<ref_time>\d{12})-(?P<lead_time>\d+)-")

    def extract_key(url: str) -> tuple[dt.datetime, dt.timedelta]:
        path = urlparse(url).path
        match = pattern.search(path)
        if not match:
            raise ValueError(f"No valid datetime found in URL path: {url}")
        val = match.group("ref_time")
        fmt = "%Y%m%d%H%M"
        utc = dt.timezone.utc
        ref_time = dt.datetime.strptime(val, fmt).replace(tzinfo=utc)
        lead_time = dt.timedelta(hours=float(match.group("lead_time")))
        return ref_time, lead_time

    asset_map = {extract_key(url): url for url in result}

    # gather reference times for which all requested lead times are present
    tmp: dict[dt.datetime, list[dt.timedelta]] = {}
    for ref_time, lead_time in asset_map:
        tmp.setdefault(ref_time, []).append(lead_time)
    required = set(lead_times)
    complete = [ref_time for ref_time in tmp if set(tmp[ref_time]) >= required]

    if request.reference_datetime == "latest":
        ref_time = max(complete)
        return [asset_map[(ref_time, lead_time)] for lead_time in lead_times]

    return [
        asset_map[(ref_time, lead_time)]
        for lead_time in lead_times
        for ref_time in complete
    ]


@lru_cache
def _get_collection_assets(collection_id: str):
    url = f"{API_URL}/collections/{collection_id}/assets"

    response = session.get(url)
    response.raise_for_status()

    return {asset["id"]: asset for asset in response.json().get("assets", [])}


def get_collection_asset_url(collection_id: str, asset_id: str) -> str:
    """Get collection asset URL from OGD.

    Query the STAC collection assets and return the URL for the given asset ID.

    Parameters
    ----------
    collection_id : str
        Full STAC collection ID
    asset_id : str
        The ID of the static asset to retrieve.

    Returns
    -------
    str
        The pre-signed URL of the requested static asset.

    Raises
    ------
    KeyError
        If the asset is not found in the collection.

    """
    assets = _get_collection_assets(collection_id)
    asset_info = assets.get(asset_id)

    if not asset_info or "href" not in asset_info:
        raise KeyError(f"Asset '{asset_id}' not found in collection '{collection_id}'.")

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

    asset_urls = get_asset_urls(request)

    source = data_source.URLDataSource(urls=asset_urls)
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
    does not include the horizontal or vertical coordinates.

    Parameters
    ----------
    request : Request
        Asset search filters, must select a single asset.
    target : Path
        Target path where to save the asset, must be a directory.

    Raises
    ------
    ValueError
        when the request does not select exactly one asset.
    RuntimeError
        if the checksum verification fails.

    """
    if target.exists() and not target.is_dir():
        raise ValueError(f"target: {target} must be a directory")

    if not target.exists():
        target.mkdir(parents=True)

    # Download main forecast asset
    asset_urls = get_asset_urls(request)
    for asset_url in asset_urls:
        _download_with_checksum(asset_url, target)

    model_suffix = request.collection.removeprefix("ogd-forecasting-")
    collection_id = f"ch.meteoschweiz.{request.collection}"

    # Download coordinate files
    for prefix in ["horizontal", "vertical"]:
        asset_id = f"{prefix}_constants_{model_suffix}-eps.grib2"
        url = get_collection_asset_url(collection_id, asset_id)
        _download_with_checksum(url, target)


def _file_hash(path: Path):
    hash = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(16 * 1024):
            hash.update(chunk)
    return hash.hexdigest()


def _download_with_checksum(url: str, target: Path) -> None:
    filename = Path(urlparse(url).path).name
    path = target / filename if target.is_dir() else target
    hash_path = path.with_suffix(".sha256")

    if path.exists():
        if hash_path.exists() and hash_path.read_text() == _file_hash(path):
            logger.info(f"File already exists, skipping download: {path}")
            return

    response = session.get(url, stream=True)
    response.raise_for_status()

    hash = response.headers.get("X-Amz-Meta-Sha256")
    if hash is not None:
        hash_path.write_text(hash)

    hasher = hashlib.sha256()
    with path.open("wb") as f:
        for chunk in response.iter_content(16 * 1024):
            f.write(chunk)
            hasher.update(chunk)

    if hash is not None and hash != hasher.hexdigest():
        raise RuntimeError(f"Checksum verification failed for {filename}")
