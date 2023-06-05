"""Differential operators on a regular grid."""

# Standard library
import dataclasses as dc

# Third-party
import numpy as np
import xarray as xr


@dc.dataclass
class _Slicer:
    ndim: int
    axis: int

    def __getitem__(self, ind):
        slices = [slice(None)] * self.ndim
        slices[self.axis] = ind
        return tuple(slices)


def _dxy(field: xr.DataArray, axis: int) -> np.ndarray:
    s = _Slicer(ndim=len(field.dims), axis=axis)
    df_dxy = np.empty_like(field)
    df_dxy[s[1:-1]] = 0.5 * (field[s[2:]] - field[s[:-2]])
    df_dxy[s[0]] = np.nan
    df_dxy[s[-1]] = np.nan
    return df_dxy


def dx(field: xr.DataArray) -> xr.DataArray:
    """Compute central finite difference along x-axis.

    The x-axis is assumed to be the last dimension of the array.
    The coordinates spacing is assumed to be of unit length.
    The field is assumed to be located at the mass points.
    The first and last elements in the x direction are undefined.
    The returned array is the same shape as the input array.

    Parameters
    ----------
    field: xr.DataArray
        The field for which to compute the finite difference along the x-axis.

    Returns
    -------
    xr.DataArray
        The finite difference of the field along the x-axis.

    """
    return field.copy(data=_dxy(field, axis=-1))


def dy(field: xr.DataArray) -> xr.DataArray:
    """Compute central finite difference along y-axis.

    The y-axis is assumed to be the last dimension of the array.
    The coordinates spacing is assumed to be of unit length.
    The field is assumed to be located at the mass points.
    The first and last elements in the y direction are undefined.
    The returned array is the same shape as the input array.

    Parameters
    ----------
    field: xr.DataArray
        The field for which to compute the finite difference along the y-axis.

    Returns
    -------
    xr.DataArray
        The finite difference of the field along the y-axis.

    """
    return field.copy(data=_dxy(field, axis=-2))


def dz(field: xr.DataArray) -> xr.DataArray:
    """Compute central finite difference along z-axis.

    The z-axis is assumed to be the third to last dimension of the array.
    The coordinates spacing is assumed to be of unit length.
    The field is assumed to be located at the mass points.
    The first and last elements in the z direction are computed using a first order
    scheme.
    The returned array is the same shape as the input array.

    Parameters
    ----------
    field: xr.DataArray
        The field for which to compute the finite difference along the z-axis.

    Returns
    -------
    xr.DataArray
        The finite difference of the field along the z-axis.

    """
    return field.copy(data=np.gradient(field, axis=-3))


def dz_staggered(field: xr.DataArray) -> xr.DataArray:
    """Compute central finite difference along z-axis on staggered field.

    The z-axis is assumed to be the third to last dimension of the array.
    The coordinates spacing is assumed to be of unit length.
    The field is assumed to be located at staggered positions in the z direction.
    The returned array is located on the mass points.

    Parameters
    ----------
    field: xr.DataArray
        The field for which to compute the finite difference along the z-axis.

    Returns
    -------
    xr.DataArray
        The finite difference of the field along the z-axis.

    """
    z = "generalVertical"
    return field.diff(dim=z, label="lower").rename({z: "generalVerticalLayer"})
