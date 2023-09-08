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


def get_nsteps(valid_time: xr.DataArray, dtime: np.timedelta64) -> int:
    """Compute number of steps required for a given time delta.

    Parameters
    ----------
    valid_time : xr.DataArray
        Array of time values.
    dtime : np.timedelta64
        Time difference for which to search the corresponding number of steps.

    Raises
    ------
    ValueError
        if the time difference is not a multiple of the given time index step or
        if the array of time values is not uniform.

    Returns
    -------
    int
        Number of time steps.

    """
    dt = valid_time.diff(dim="time")
    uniform = np.all(dt == dt[0]).item()

    if not uniform:
        msg = "Given field has an irregular time step."
        raise ValueError(msg)

    condition = valid_time - valid_time[0] == dtime
    try:
        [index] = np.nonzero(condition.values)
    except ValueError:
        msg = "Provided dtime is not a multiple of the time step."
        raise ValueError(msg)

    return index.item()


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
        if dtime is not multiple of the field time step
        or if the time step is not regular.

    Returns
    -------
    xr.DataArray
        The field difference for the given time delta.

    """
    nsteps = get_nsteps(field.valid_time, dtime)
    result = field - field.shift(time=nsteps)
    result.attrs = field.attrs
    return result


def resample_average(field: xr.DataArray, dtime: np.timedelta64) -> xr.DataArray:
    """Compute weighted difference for a given delta in time.

    This operator is useful for recomputing time averaged values that are
    aggregated from the reference time to the lead time. The output field
    is averaged with respect to the given time interval for every lead time
    present in the input field. The output for lead times that are smaller
    than the reference time shifted by the interval are undefined.

    Note that this operator is named tdelta in fieldextra.

    Parameters
    ----------
    field : xr.DataArray
        Field that contains the input data.
    dtime : np.timedelta64
        Time delta for which to evaluate the difference.

    Raises
    ------
    ValueError
        if dtime is not multiple of the field time step
        or if the time step is not regular.

    Returns
    -------
    xr.DataArray
        The field weighted difference for the given time delta.

    """
    nsteps = get_nsteps(field.valid_time, dtime)
    weights = (field.valid_time - field.ref_time) / dtime
    weighted = field * weights
    result = weighted - weighted.shift(time=nsteps)
    result.attrs = field.attrs
    return result


def resample(field: xr.DataArray, interval: np.timedelta64) -> xr.DataArray:
    """Resample field.

    The interval must be a multiple of the current time step.
    No interpolation is performed.

    Parameters
    ----------
    field : xr.DataArray
        Field that contains the input data.
    interval : np.timedelta64
        Output sample interval.

    Raises
    ------
    ValueError
        if dtime is not multiple of the field time step
        or if the time step is not regular.

    Returns
    -------
    xr.DataArray
        The resampled field.

    """
    nsteps = get_nsteps(field.valid_time, interval)
    return field.sel(time=slice(None, None, nsteps))
