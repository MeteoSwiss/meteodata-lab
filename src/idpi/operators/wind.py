"""Wind operators."""

# Third-party
import numpy as np
import xarray as xr

# Local
from ..metadata import override
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
    if u.origin_x != 0.0 or v.origin_y != 0.0:
        raise ValueError("The wind components should not be staggered.")

    name = {"U": "SP", "U_10M": "SP_10M"}[u.parameter["shortName"]]
    return xr.DataArray(
        np.sqrt(u**2 + v**2),
        attrs=override(u.message, shortName=name),
    )


def direction(u: xr.DataArray, v: xr.DataArray) -> xr.DataArray:
    """Compute the horizontal wind direction.

    Note that terrain following grid deformation is not accounted for.
    The input fields are required to be located on the mass points
    of a regular grid defined in the rotated latlon coordinate system.
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
        other than a regular grid in the rotated latlon coordinate system.

    Returns
    -------
    xarray.DataArray
        the horizontal wind direction with respect to geographic North [deg].

    """
    rad2deg = 180 / np.pi
    u_g, v_g = vref_rot2geolatlon(u, v)
    name = {"U": "DD", "U_10M": "DD_10M"}[u.parameter["shortName"]]
    return xr.DataArray(
        rad2deg * np.arctan2(u_g, v_g) + 180,
        attrs=override(u.message, shortName=name),
    )
