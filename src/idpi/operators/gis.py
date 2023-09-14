"""Geospatial logic."""

# Standard library
import dataclasses as dc
import typing
from collections.abc import Mapping

# Third-party
import numpy as np
import xarray as xr

# Local
from .support_operators import get_grid_coords


@dc.dataclass
class RotLatLonGrid:
    """Class representing a rotated lat lon grid.

    Attributes
    ----------
    rlon : xr.DataArray
        longitude values in degrees of the grid points in the rotated lat lon CRS.
    rlat : xr.DataArray
        latitude values in degrees of the grid points in the rotated lat lon CRS.
    north_pole_lon : float
        longitude of the rotated north pole in degrees.
    north_pole_lat : float
        latitude of the rotated north pole in degrees.

    """

    # all units in degrees
    rlon: xr.DataArray
    rlat: xr.DataArray
    north_pole_lon: float
    north_pole_lat: float


def _check_requirements(geo: Mapping[str, typing.Any]) -> None:
    requirements = {
        "angleOfRotationInDegrees": 0.0,
        "gridType": "rotated_ll",
        "iScansNegatively": 0,
        "jScansPositively": 1,
    }
    errors = {key: geo[key] for key in requirements if requirements[key] != geo[key]}
    if errors:
        msg = f"Unsupported values for keys: {errors}"
        raise ValueError(msg)


def get_grid(geo: Mapping[str, typing.Any]) -> RotLatLonGrid:
    """Get grid parameters for a given field.

    Only fields defined on regular grids in rotlatlon coordinates,
    without rotation nor flipped axes are supported.

    Parameters
    ----------
    geo : Mapping[str, Any]
        Grib keys related to the geography of the field.

    Raises
    ------
    ValueError
        if the field does not fulfill the conditions above.

    Returns
    -------
    RotLatLonGrid
        object representing the rotated lat lon grid.

    """
    _check_requirements(geo)

    ni = geo["Ni"]
    x0 = geo["longitudeOfFirstGridPointInDegrees"]
    dx = geo["iDirectionIncrementInDegrees"]
    rlon = get_grid_coords(ni, x0, dx, "x")

    nj = geo["Nj"]
    y0 = geo["latitudeOfFirstGridPointInDegrees"]
    dy = geo["jDirectionIncrementInDegrees"]
    rlat = get_grid_coords(nj, y0, dy, "y")

    lon_np = (geo["longitudeOfSouthernPoleInDegrees"] - 180) % 360
    lat_np = -1 * geo["latitudeOfSouthernPoleInDegrees"]

    return RotLatLonGrid(rlon, rlat, lon_np, lat_np)


def rot2geolatlon(grid: RotLatLonGrid) -> tuple[xr.DataArray, xr.DataArray]:
    """Compute geographical lat lon values for a rotated lat lon grid.

    Parameters
    ----------
    grid : RotLatLonGrid
        object representing the rotated lat lon grid.

    Returns
    -------
    tuple[xarray.DataArray, xarray.DataArray]
        tuple of longitudes and latitudes of the grid points in the
        geographical lat lon CRS.

    """
    deg2rad = np.pi / 180
    rad2deg = 180 / np.pi
    sin_np_lat = np.sin(deg2rad * grid.north_pole_lat)
    cos_np_lat = np.cos(deg2rad * grid.north_pole_lat)

    sin_np_lon = np.sin(deg2rad * grid.north_pole_lon)
    cos_np_lon = np.cos(deg2rad * grid.north_pole_lon)

    # Compute new coordinates
    # ... normalize input coordinates
    norm_lon = deg2rad * grid.rlon.where(grid.rlon < 180, grid.rlon - 360)

    # ... cache trigonometric operations
    sin_lat = np.sin(deg2rad * grid.rlat)
    cos_lat = np.cos(deg2rad * grid.rlat)
    sin_lon = np.sin(norm_lon)
    cos_lon = np.cos(norm_lon)
    # ... compute latitude
    arg1 = cos_np_lat * cos_lat * cos_lon + sin_np_lat * sin_lat
    lat = rad2deg * np.arcsin(arg1)
    # ... compute longitude
    arg2 = (
        sin_np_lon * (-sin_np_lat * cos_lon * cos_lat + cos_np_lat * sin_lat)
        - cos_np_lon * sin_lon * cos_lat
    )
    arg3 = (
        cos_np_lon * (-sin_np_lat * cos_lon * cos_lat + cos_np_lat * sin_lat)
        + sin_np_lon * sin_lon * cos_lat
    )
    # BUG: changes sign when arg2 is negative and less than threshold
    arg4 = xr.where(np.abs(arg3) < 1e-20, 1e-20, arg3)
    lon = rad2deg * np.arctan2(arg2, arg4) % 360

    return lon, lat


def geolatlon2swiss(
    lon: xr.DataArray, lat: xr.DataArray
) -> tuple[xr.DataArray, xr.DataArray]:
    """Convert from geolatlon to swiss coordinates.

    Parameters
    ----------
    lon : xarray.DataArray
        longitude coordinates in the geolatlon CRS.
    lat : xarray.DataArray
        latitude coordinates in the geolatlon CRS.

    Returns
    -------
    tuple[xarray.DataArray, xarray.DataArray]
        x and y coordinates in the Swiss LV03 coordinate system.

    Notes
    -----
    Approximate formula published by swisstopo, precision in the order of 1 meter

    """
    norm_lat = ((lat * 3.6) - 169.02866) / 10
    lon = lon.where(lon < 180, lon - 360)
    norm_lon = ((lon * 3.6) - 26.7825) / 10
    y = (
        200147.07
        + 3745.25 * norm_lon * norm_lon
        + norm_lat
        * (
            308807.95
            + 76.63 * norm_lat
            - 194.56 * norm_lon * norm_lon
            + 119.79 * norm_lat * norm_lat
        )
    )
    x = 600072.37 + norm_lon * (
        211455.93
        - 10938.51 * norm_lat
        - 0.36 * norm_lat * norm_lat
        - 44.54 * norm_lon * norm_lon
    )
    return x, y


def vref_rot2geolatlon(
    u: xr.DataArray, v: xr.DataArray
) -> tuple[xr.DataArray, xr.DataArray]:
    """Apply coordinate rotation to vector field.

    When converting from rotated lat lon to geo lat lon, the
    orientation of the grid changes and vector fields for which
    the components are expressed in the grid unit vectors need
    to be realigned.

    Note that this function does not perform any regridding.

    Parameters
    ----------
    u : xarray.DataArray
        x component of the vector field w.r.t. a rotated lat lon grid.
    v : xarray.DataArray
        y component of the vector field w.r.t. a rotated lat lon grid.

    Returns
    -------
    tuple[xarray.DataArray, xarray.DataArray]
        x and y components of the vector field w.r.t. the geo lat lon coords.

    """
    valid_origin = {d: 0.0 for d in tuple("xyz")}
    if u.origin != valid_origin or v.origin != valid_origin:
        raise ValueError("The vector fields must be destaggered.")

    grid = get_grid(u.geography)
    lon, lat = rot2geolatlon(grid)
    return _vref_rot2geolatlon(u, v, lon, lat, grid)


def _vref_rot2geolatlon(
    u: xr.DataArray,
    v: xr.DataArray,
    lon: xr.DataArray,
    lat: xr.DataArray,
    grid: RotLatLonGrid,
) -> tuple[xr.DataArray, xr.DataArray]:
    deg2rad = np.pi / 180
    sin_np = np.sin(deg2rad * grid.north_pole_lat)
    cos_np = np.cos(deg2rad * grid.north_pole_lat)

    norm_lat = lat * deg2rad
    norm_dlon = (grid.north_pole_lon - lon) * deg2rad
    arg1 = cos_np * np.sin(norm_dlon)
    arg2 = sin_np * np.cos(norm_lat) - cos_np * np.sin(norm_lat) * np.cos(norm_dlon)
    norm = 1.0 / np.sqrt(arg1**2 + arg2**2)

    u_out = u * arg2 * norm + v * arg1 * norm
    v_out = -u * arg1 * norm + v * arg2 * norm

    return u_out, v_out
