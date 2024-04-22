"""Horizontal cropping operator."""

# Standard library
import typing

# Third-party
import numpy as np
import xarray as xr

# Local
from .. import metadata
from . import gis


class Bounds(typing.NamedTuple):
    xmin: int
    xmax: int
    ymin: int
    ymax: int


def crop(field: xr.DataArray, bounds: Bounds) -> xr.DataArray:
    """Crop the field to the given bounds.

    Only fields defined on regular grids in rotlatlon coordinates,
    without rotation nor flipped axes are supported.

    Parameters
    ----------
    field : xarray.DataArray
        The field to crop.
    bounds : Bounds
        Bounds of the cropped area given as indices of the array in following order:
        xmin, xmax, ymin, ymax.
        All bounds are inclusive.

    Raises
    ------
    ValueError
        If there are any consistency issues with the provided bounds
        or any of the conditions on the input grid not met.

    Returns
    -------
    xarray.DataArray
        The data is set to cropped domain and the metadata is updated accordingly.

    """
    xmin, xmax, ymin, ymax = bounds

    sizes = field.sizes
    if (
        xmin > xmax
        or ymin > ymax
        or any(v < 0 for v in bounds)
        or xmax >= sizes["x"]
        or ymax >= sizes["y"]
    ):
        raise ValueError(f"Inconsistent bounds: {bounds}")

    grid = gis.get_grid(field.geography)
    lon_min, lon_max = np.round(grid.rlon.isel(x=[xmin, xmax]).values * 1e6)
    lat_min, lat_max = np.round(grid.rlat.isel(y=[ymin, ymax]).values * 1e6)
    ni = xmax - xmin + 1
    nj = ymax - ymin + 1
    npts = ni * nj

    return xr.DataArray(
        field.isel(x=slice(xmin, xmax + 1), y=slice(ymin, ymax + 1)),
        attrs=metadata.override(
            field.message,
            longitudeOfFirstGridPoint=lon_min,
            longitudeOfLastGridPoint=lon_max,
            Ni=ni,
            latitudeOfFirstGridPoint=lat_min,
            latitudeOfLastGridPoint=lat_max,
            Nj=nj,
            numberOfDataPoints=npts,
        ),
    )
