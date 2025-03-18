"""Wind operators."""

# Third-party
import numpy as np
import xarray as xr

# Local
from ..metadata import is_staggered, override
from .gis import vref_rot2geolatlon


def speed(u: xr.DataArray, v: xr.DataArray) -> xr.DataArray:
    """Compute the horizontal wind speed.

    Note that terrain following grid deformation is not accounted for.
    The input fields are required to be located on the mass points.
    The preferred unit is meters per second but any consistent unit system
    acceptable.

    Parameters
    ----------
    u : xarray.DataArray
        the x component of the wind velocity [m/s].
    v : xarray.DataArray
        the y component of the wind velocity [m/s].

    Raises
    ------
    ValueError
        if any of the input fields is located on staggered points.

    Returns
    -------
    xarray.DataArray
        the horizontal wind speed [m/s].

    """
    if is_staggered(u) or is_staggered(v):
        raise ValueError("The wind components should not be staggered.")

    name = {"U": "SP", "U_10M": "SP_10M"}[u.parameter["shortName"]]
    return xr.DataArray(
        np.sqrt(u**2 + v**2),
        attrs=override(u.metadata, shortName=name),
    )


def direction(u: xr.DataArray, v: xr.DataArray) -> xr.DataArray:
    """Compute the horizontal wind direction.

    Note that terrain following grid deformation is not accounted for.
    The input fields are required to be located on the mass points
    of a grid defined in the rotated or geo latlon coordinate system.
    The preferred unit is meters per second but any consistent unit system
    acceptable.

    Parameters
    ----------
    u : xarray.DataArray
        the x component of the wind velocity [m/s].
    v : xarray.DataArray
        the y component of the wind velocity [m/s].

    Raises
    ------
    ValueError
        if any of the input fields is located on staggered points or on any
        other than a grid in the rotated or geo latlon coordinate system.

    Returns
    -------
    xarray.DataArray
        the horizontal wind direction with respect to geographic North [deg].

    """
    rad2deg = 180 / np.pi
    if u.vref == "geo" and v.vref == "geo":
        u_g = u
        v_g = v
    else:
        u_g, v_g = vref_rot2geolatlon(u, v)
    name = {"U": "DD", "U_10M": "DD_10M"}[u.parameter["shortName"]]
    return xr.DataArray(
        rad2deg * np.arctan2(u_g, v_g) + 180,
        attrs=override(u.metadata, shortName=name),
    )
