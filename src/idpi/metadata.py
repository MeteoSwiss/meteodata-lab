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


def override(message: bytes, **kwargs: typing.Any) -> dict[str, typing.Any]:
    """Override GRIB metadata contained in message.

    Note that no special consideration is made for maintaining consistency when
    overriding template definition keys such as productDefinitionTemplateNumber.

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
        "geography": md.as_namespace("geography"),
        "parameter": md.as_namespace("parameter"),
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
        "x": np.round((geo[x0_key] % 360 - x0) / dx, 1),
        "y": np.round((geo[y0_key] - y0) / dy, 1),
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
        field.attrs["origin"] |= compute_origin(ref_grid, field)
