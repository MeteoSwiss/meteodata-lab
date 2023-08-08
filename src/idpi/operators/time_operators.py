"""Various time operators."""
# Third-party
import numpy as np
import xarray as xr


def time_rate(var: xr.DataArray, dtime: np.timedelta64):
    """Compute a time rate for a given delta in time.

    It assumes the input data is an accumulated value
    between two time steps of the time coordinate

    Args:
        var: variable that contains the input data
        dtime: delta time of the desired output time rate

    """
    coord = var.valid_time
    result = var.diff(dim="time") / (coord.diff(dim="time") / dtime)
    result.attrs = var.attrs
    return result


def delta(field: xr.DataArray, dtime: np.timedelta64) -> xr.DataArray:
    """Compute difference for a given delta in time.

    Parameters
    ----------
    field : xr.DataArray
        Field that contains the input data.
    dtime : np.timedelta64
        Time delta for which to evaluate the difference.

    Raises
    ------
    ValueError
        if dtime is not multiple of the field time step.

    Returns
    -------
    xr.DataArray
        The Field difference for the given time delta.

    """
    coord = field.valid_time
    condition = coord - coord[0] == dtime

    try:
        [index] = np.nonzero(condition.values)
    except ValueError:
        msg = "Provided dtime is not a multiple of the time step."
        raise ValueError(msg)

    result = field - field.shift(time=index.item())
    result.attrs = field.attrs
    return result
