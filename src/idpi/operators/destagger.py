"""algorithm for destaggering a field."""

# Standard library
from typing import Any, Literal

# Third-party
import numpy as np
import xarray as xr

# Local
from .. import metadata

ExtendArg = Literal["left", "right", "both"] | None


def _intrp_mid(a: np.ndarray) -> np.ndarray:
    return 0.5 * (a[..., :-1] + a[..., 1:])


def _left(a: np.ndarray) -> np.ndarray:
    t = a.copy()
    t[..., 1:] = _intrp_mid(a)
    return t


def _right(a: np.ndarray) -> np.ndarray:
    t = a.copy()
    t[..., :-1] = _intrp_mid(a)
    return t


def _both(a: np.ndarray) -> np.ndarray:
    *m, n = a.shape
    t = np.empty((*m, n + 1))
    t[..., 0] = a[..., 0]
    t[..., -1] = a[..., -1]
    t[..., 1:-1] = _intrp_mid(a)
    return t


def interpolate_midpoint(array: np.ndarray, extend: ExtendArg = None) -> np.ndarray:
    """Interpolate field values onto the midpoints.

    The interpolation is only done on the last dimension of the given array.
    The first or last values can optionally duplicated as per the extend argument.

    Parameters
    ----------
    array : np.ndarray
        Array of field values
    extend : None | Literal["left", "right", "both"]
        Optionally duplicate values on the left, right or both sides.
        Defaults to None.

    Raises
    ------
    ValueError
        If the extend argument is not recognised.

    Returns
    -------
    np.ndarray
        Values of the field interpolated to the midpoint on the last dimension.

    """
    f_map = {
        None: _intrp_mid,
        "left": _left,
        "right": _right,
        "both": _both,
    }
    if extend not in f_map:
        raise ValueError(f"extend arg not in {tuple(f_map.keys())}")
    return f_map[extend](array)


def _update_grid(field: xr.DataArray, dim: Literal["x", "y"]) -> dict[str, Any]:
    geo = field.geography
    if dim == "x":
        lon_min = np.round(geo["longitudeOfFirstGridPointInDegrees"] * 1e6)
        lon_max = np.round(geo["longitudeOfLastGridPointInDegrees"] * 1e6)
        dx = np.round(geo["iDirectionIncrementInDegrees"] * 1e6)
        return metadata.override(
            field.message,
            longitudeOfFirstGridPoint=lon_min - dx / 2,
            longitudeOfLastGridPoint=lon_max - dx / 2,
        )
    if dim == "y":
        lat_min = np.round(geo["latitudeOfFirstGridPointInDegrees"] * 1e6)
        lat_max = np.round(geo["latitudeOfLastGridPointInDegrees"] * 1e6)
        dy = np.round(geo["jDirectionIncrementInDegrees"] * 1e6)
        return metadata.override(
            field.message,
            latitudeOfFirstGridPoint=lat_min - dy / 2,
            latitudeOfLastGridPoint=lat_max - dy / 2,
        )


def _update_vertical(field) -> dict[str, Any]:
    if field.vcoord_type != "model_level":
        raise ValueError("typeOfLevel must equal generalVertical")
    return metadata.override(
        field.message,
        typeOfLevel="generalVerticalLayer",
    )


def destagger(
    field: xr.DataArray,
    dim: Literal["x", "y", "z"],
) -> xr.DataArray:
    """Destagger a field.

    Note that, in the x and y directions, it is assumed that one element
    of the destaggered field is missing on the left side of the domain.
    The first element is thus duplicated to fill the blank.

    Parameters
    ----------
    field : xr.DataArray
        Field to destagger
    dim : Literal["x", "y", "z"]
        Dimension along which to destagger

    Raises
    ------
    ValueError
        Raises ValueError if dim argument is not one of
        {"x","y","z"}.

    Returns
    -------
    xr.DataArray
        destaggered field with dimensions in
        {"x","y","z"}

    """
    dims = list(field.sizes.keys())
    if dim == "x" or dim == "y":
        if field.attrs[f"origin_{dim}"] != 0.5:
            raise ValueError
        return (
            xr.apply_ufunc(
                interpolate_midpoint,
                field.reset_coords(drop=True),
                input_core_dims=[[dim]],
                output_core_dims=[[dim]],
                kwargs={"extend": "left"},
                keep_attrs=True,
            )
            .transpose(*dims)
            .assign_attrs({f"origin_{dim}": 0.0}, **_update_grid(field, dim))
        )
    elif dim == "z":
        if field.origin_z != -0.5:
            raise ValueError
        return (
            xr.apply_ufunc(
                interpolate_midpoint,
                field,
                input_core_dims=[[dim]],
                output_core_dims=[[dim]],
                exclude_dims={dim},
                keep_attrs=True,
            )
            .transpose(*dims)
            .assign_attrs({f"origin_{dim}": 0.0}, **_update_vertical(field))
        )

    raise ValueError("Unknown dimension", dim)
