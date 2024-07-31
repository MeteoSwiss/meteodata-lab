"""Relative humidity operators."""

# Standard library
from typing import Literal

# Third-party
import xarray as xr

# Local
from .. import metadata
from .atmo import pv_si, pv_sm, pv_sw, qv_pvp


def relhum(
    qv, t, p, clipping=True, phase: Literal["water", "ice", "water+ice"] = "water"
):
    """Calculate relative humidity.

    Parameters
    ----------
    qv : xarray.DataArray
        water vapor mixing ratio
    t : xarray.DataArray
        temperature in Kelvin
    p : xarray.DataArray
        pressure in Pa
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
    xarray.DataArray
        relative humidity field in %

    """
    max = 100 if clipping else None

    phase_conditions = {
        "water": {"func": pv_sw(t), "shortName": "RELHUM"},
        "ice": {"func": pv_si(t), "shortName": "RH_ICE"},
        "water+ice": {"func": pv_sm(t), "shortName": "RH_MIX_EC"},
    }

    if phase not in phase_conditions:
        raise ValueError("Invalid phase. Phase must be 'water', 'ice', or 'water+ice'.")

    result = (100.0 * qv / qv_pvp(phase_conditions[phase]["func"], p)).clip(0, max)

    return xr.DataArray(
        data=result,
        attrs=metadata.override(
            t.message, shortName=phase_conditions[phase]["shortName"]
        ),
    )
