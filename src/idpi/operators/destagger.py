"""algorithm for destaggering a field."""
# Third-party
import numpy as np
import xarray as xr


def _dstgr(a: np.ndarray):
    t = a.copy()
    t[..., 1:] = 0.5 * (a[..., :-1] + a[..., 1:])
    return t


def _dstgr_z(a: np.ndarray):
    return 0.5 * (a[..., :-1] + a[..., 1:])


def destagger(field: xr.DataArray, dim: str) -> xr.DataArray:
    """Destagger a field.

    Args:
        field (xr.DataArray): field to destagger
        dim (str): dimension, one of {"x", "y", "generalVertical"}

    Raises:
        RuntimeError: todo: describe this

    Returns:
        xr.DataArray: destaggered field with dimensions in
            {"x","y","generalVerticalLayer"}

    """
    dims = list(field.sizes.keys())
    if dim == "x" or dim == "y":
        return xr.apply_ufunc(
            _dstgr,
            field.reset_coords(drop=True),
            input_core_dims=[[dim]],
            output_core_dims=[[dim]],
        ).transpose(*dims)
    elif dim == "generalVertical":
        return (
            xr.apply_ufunc(
                _dstgr_z,
                field,
                input_core_dims=[[dim]],
                output_core_dims=[[dim]],
                exclude_dims={dim},
            )
            .transpose(*dims)
            .assign_coords({dim: field.generalVertical[:-1]})
            .rename({"generalVertical": "generalVerticalLayer"})
        )

    raise RuntimeError("Unknown dimension", dim)
