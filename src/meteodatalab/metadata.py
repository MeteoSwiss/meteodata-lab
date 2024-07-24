"""Manage GRIB metadata."""

# Standard library
import dataclasses as dc
import io
import typing

# Third-party
import earthkit.data as ekd  # type: ignore
import numpy as np
import xarray as xr
from earthkit.data.writers import write  # type: ignore

# Local
from . import grib_decoder

VCOORD_TYPE = {
    "generalVertical": ("model_level", -0.5),
    "generalVerticalLayer": ("model_level", 0.0),
    "isobaricInPa": ("pressure", 0.0),
}


def extract(metadata):
    [vref_flag] = grib_decoder.get_code_flag(
        metadata.get("resolutionAndComponentFlags"), [5]
    )
    level_type = metadata.get("typeOfLevel")
    vcoord_type, zshift = VCOORD_TYPE.get(level_type, (level_type, 0.0))

    return {
        "parameter": metadata.as_namespace("parameter"),
        "geography": metadata.as_namespace("geography"),
        "vref": "native" if vref_flag else "geo",
        "vcoord_type": vcoord_type,
        "origin_z": zshift,
    }


def override(message: bytes, **kwargs: typing.Any) -> dict[str, typing.Any]:
    """Override GRIB metadata contained in message.

    Note that no special consideration is made for maintaining consistency when
    overriding template definition keys such as productDefinitionTemplateNumber.
    Note that the origin components in x and y are left untouched.

    Parameters
    ----------
    message : bytes
        Byte string of the input GRIB message
    kwargs : Any
        Keyword arguments forwarded to earthkit-data GribMetadata override method

    Returns
    -------
    dict[str, Any]
        Updated message byte string along with the geography and parameter namespaces

    """
    stream = io.BytesIO(message)
    [grib_field] = ekd.from_source("stream", stream)

    out = io.BytesIO()
    md = grib_field.metadata().override(**kwargs)
    write(out, grib_field.values, md)

    return {
        "message": out.getvalue(),
        **extract(md),
    }


@dc.dataclass
class Grid:
    """Coordinates of the reference grid.

    Attributes
    ----------
    lon_first_grid_point: float
        longitude of first grid point in rotated lat-lon CRS
    lat_first_grid_point: float
        latitude of first grid point in rotated lat-lon CRS

    """

    lon_first_grid_point: float
    lat_first_grid_point: float


def load_grid_reference(message: bytes) -> Grid:
    """Construct a grid from a reference parameter.

    Parameters
    ----------
    message : bytes
        GRIB message defining the reference grid.

    Returns
    -------
    Grid
        reference grid

    """
    stream = io.BytesIO(message)
    [grib_field] = ekd.from_source("stream", stream)

    return Grid(
        *grib_field.metadata(
            "longitudeOfFirstGridPointInDegrees",
            "latitudeOfFirstGridPointInDegrees",
        ),
    )


def compute_origin(ref_grid: Grid, field: xr.DataArray) -> dict[str, float]:
    """Compute horizontal components of the origin dict.

    Parameters
    ----------
    ref_grid : Grid
        reference grid
    field : xarray.DataArray
        field for which to compute the origin

    Returns
    -------
    dict[str, float]
        Horizontal components of the origin

    """
    x0 = ref_grid.lon_first_grid_point % 360
    y0 = ref_grid.lat_first_grid_point
    geo = field.geography
    dx = geo["iDirectionIncrementInDegrees"]
    dy = geo["jDirectionIncrementInDegrees"]
    x0_key = "longitudeOfFirstGridPointInDegrees"
    y0_key = "latitudeOfFirstGridPointInDegrees"

    return {
        "origin_x": np.round((geo[x0_key] % 360 - x0) / dx, 1),
        "origin_y": np.round((geo[y0_key] - y0) / dy, 1),
    }


def set_origin_xy(ds: dict[str, xr.DataArray], ref_param: str) -> None:
    """Set horizontal components of the origin attribute.

    Parameters
    ----------
    ds : dict[str, xarray.DataArray]
        Dataset of fields to update.
    ref_param : str
        Name of the parameter field to use as a reference. Must be a key of ds.

    Raises
    ------
    KeyError
        if the ref_param key is not found in the input dataset

    """
    if ref_param not in ds:
        raise KeyError(f"ref_param {ref_param} not present in dataset.")

    ref_grid = load_grid_reference(ds[ref_param].message)
    for field in ds.values():
        field.attrs |= compute_origin(ref_grid, field)


def extract_pv(message: bytes) -> dict[str, xr.DataArray]:
    """Extract hybrid level coefficients.

    Parameters
    ----------
    message : bytes
        GRIB message containing the pv metadata.

    Returns
    -------
    dict[str, xarray.DataArray]
        Hybrid level coefficients.

    """
    stream = io.BytesIO(message)
    [grib_field] = ekd.from_source("stream", stream)

    pv = grib_field.metadata("pv")

    if pv is None:
        return {}

    i = len(pv) // 2
    return {
        "ak": xr.DataArray(pv[:i], dims="z"),
        "bk": xr.DataArray(pv[i:], dims="z"),
    }


def extract_hcoords(message: bytes) -> dict[str, xr.DataArray]:
    """Extract horizontal coordinates.

    Parameters
    ----------
    message : bytes
        GRIB message containing the grid definition.

    Returns
    -------
    dict[str, xarray.DataArray]
        Horizontal coordinates in geolatlon.

    """
    stream = io.BytesIO(message)
    [grib_field] = ekd.from_source("stream", stream)

    return {
        dim: xr.DataArray(dims=("y", "x"), data=values)
        for dim, values in grib_field.to_latlon().items()
    }


def extract_keys(message: bytes, keys: typing.Any) -> typing.Any:
    """Extract keys from the GRIB message.

    Parameters
    ----------
    message : bytes
        The GRIB message.
    keys : Any
        Keys for which to extract values from the message.

    Raises
    ------
    ValueError
        if keys is None because the resulting metadata would point
        to an eccodes handle that no longer exists resulting in a
        possible segmentation fault

    Returns
    -------
    Any
        Single value if keys is a single value, tuple of values if
        keys is a tuple, list of values if keys is a list. The type of
        the value depends on the default type for the given key in eccodes.
    """
    if keys is None:
        raise ValueError("keys must be specified.")
    stream = io.BytesIO(message)
    [grib_field] = ekd.from_source("stream", stream)
    return grib_field.metadata(keys)
