"""Lateral operators."""

# Standard library
from typing import Literal

# Third-party
import numpy as np
import xarray as xr


def compute_weights(
    window_size: int,
    window_type: Literal["exp", "const"],
    window_shape: Literal["disk", "square"],
) -> xr.DataArray:
    """Compute weights for a convolution kernel.

    Parameters
    ----------
    window_size : int
        Number of grid cells the kernel. Must be an odd number.
    window_type : {"exp", "const"}
        The window type.

        Supported types:
         - exp: Exponential drop from the center of the window.
         - const: All weights are set to 1.

    window_shape : {"disk", "square"}
        The window shape.

        Supported shapes:
         - disk: The kernel is confined to the circle inscribing the window.
         - square: The kernel is defined on the entire window.

    Raises
    ------
    ValueError
        if `window_size` is not an odd number.

    Returns
    -------
    xarray.DataArray
        Weights corresponding to the `window_type` within the given `window_shape`
        and zero outside of the shape.

    """
    n = window_size

    if n % 2 != 1:
        raise ValueError("window_size must be an odd number.")

    radius = n // 2
    yy, xx = np.mgrid[:n, :n] - radius
    dist = np.sqrt(xx**2 + yy**2)

    if window_type == "exp":
        kernel = np.exp(-dist)
    else:
        kernel = np.ones((n, n))

    weights = xr.DataArray(kernel, dims=["win_x", "win_y"])

    if window_shape == "disk":
        return weights.where(dist <= radius, 0.0)

    return weights


def compute_cond_mask(
    windows: xr.DataArray, weights: xr.DataArray, frac_val: float, nx: int, ny: int
) -> xr.DataArray:
    """Compute the conditional mask for which the convolution results are valid.

    The function computes the ratio of undefined values to the total number values
    in the convolution window. The computational domain and the window shape are both
    taken into account. The mask is true for locations where the ratio is above the
    given threshold.

    Parameters
    ----------
    windows : xarray.DataArray
        Values of the constructed windows for the application of the convolution.
    weights : xarray.DataArray
        Weights of the convolution kernel.
    frac_val : float
        Threshold on the ratio of undefined values.
    nx : int
        Size of the field in the x dimension.
    ny : int
        Size of the field in the y dimension.

    Returns
    -------
    xarray.DataArray
        Boolean mask indicating where the undefined value ratio in the convolution
        kernel is within the acceptable threshold.

    """
    # For each window, `x` is the coordinate of the center of the window in the parent
    # field. `win_x` is the local coordinate of the current element in the window.
    # `loc_x` represents the location of the window element in the coordinates of the
    # parent field. This is needed to filter out nans that are introduced by the
    # padding of the field by the rolling method. Only the nans that are present within
    # the bound of the field should count towards the `frac_val` threshold.

    mask = weights > 0

    loc_x = windows.x + windows.win_x - windows.sizes["win_x"] // 2
    in_bnds_x = np.logical_and(0 <= loc_x, loc_x < nx)

    loc_y = windows.y + windows.win_y - windows.sizes["win_y"] // 2
    in_bnds_y = np.logical_and(0 <= loc_y, loc_y < ny)

    undef = windows.isnull()
    frac_undef = undef.where(mask).where(in_bnds_x).where(in_bnds_y).mean(weights.dims)
    return frac_undef <= frac_val


def fill_undef(field: xr.DataArray, radius: int, frac_val: float) -> xr.DataArray:
    """Fill undefined values.

    Replace undefined values with a value derived from neighbourhood.
    The values are obtained by applying a Gaussian filter to the field
    around the undefined elements.

    Parameters
    ----------
    field : xarray.DataArray
        Input field.
    radius : int
        Radius of the convolution window.
    frac_val : float
        Threshold of acceptable ratio of undefined values in window.
        If the ratio of undefined to total elements in the window is
        below the threshold then the output value remains undefined.

    Returns
    -------
    xarray.DataArray
        Input field with undefined values replaced by values derived from neighbourhood.

    """
    n = 2 * radius + 1
    weights = compute_weights(n, "exp", "disk")

    # select undefined grid elements
    undef = field.isnull()
    idx = {
        dim: xr.DataArray(idx, dims="undef")
        for dim, idx in zip(undef.dims, np.nonzero(undef.values))
    }
    xy_coords = {dim: range(field.sizes[dim]) for dim in "xy"}

    # construct rolling windows
    dims = {"x": "win_x", "y": "win_y"}
    windows = (
        field.assign_coords(xy_coords)
        .rolling({"x": n, "y": n}, center=True)
        .construct(dims)
        .sel(idx)
    )

    # compute conditional mask
    s = field.sizes
    cond = compute_cond_mask(windows, weights, frac_val, s["x"], s["y"])

    # compute weighted mean skipping undefined values
    smoothed = windows.weighted(weights).mean(dims.values())

    # replace undefined values in input field
    result = field.copy()
    result[idx] = smoothed.where(cond)
    return result


def disk_avg(field: xr.DataArray, radius: int) -> xr.DataArray:
    """Compute disk average.

    Parameters
    ----------
    field : xarray.DataArray
        Input field.
    radius : int
        Radius of the convolution window.

    Returns
    -------
    xarray.DataArray

    """
    n = 2 * radius + 1
    weights = compute_weights(n, "const", "disk")

    # construct rolling windows
    dims = {"x": "win_x", "y": "win_y"}
    windows = field.rolling({"x": n, "y": n}, center=True).construct(dims)

    # compute weighted mean skipping undefined values
    skipna = field.isnull().any().item()
    smoothed = windows.weighted(weights).mean(dims.values(), skipna=skipna)

    return smoothed.where(~field.isnull())
