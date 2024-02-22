"""Relative humidity operators."""

# Standard library
from typing import Literal

# Third-party
import xarray as xr

# First-party
from idpi.operators.atmo import pv_sw, qv_pvp


def relhum(
    qv, t, p, clipping=True, phase: Literal["water", "ice", "water+ice"] = "water"
):
    """Calculate relative humidity.

    Parameters
    ----------
    qv : xr.DataArray
        water vapor mixing ratio
    t : xr.DataArray
        temperature
    p : xr.DataArray
        pressure
    clipping : bool
        clips the relative humidity to [0,100] interval.
        Only upper bound is controlled by this parameter,
        since lower bound clipping is always performed.
    phase : Literal["water", "ice", "water+ic"]
        Customizes how relative humidity is computed.
        'water'        over water
        'ice'          over ice
        'water+ice'    over mixed phase

    Returns
    -------
    xr.DataArray
        relative humidity field

    """
    if phase != "water":
        raise ValueError(f"{phase=} not implemented")
    attrs = t.attrs.copy()
    max = 100 if clipping else None

    return xr.DataArray((100.0 * qv / qv_pvp(pv_sw(t), p)).clip(0, max), attrs=attrs)
