"""Relative humidity operators."""

# Standard library
from typing import Literal

# Third-party
import xarray as xr
from earthkit.meteo import thermo  # type: ignore

# Local
from .. import metadata


def relhum(
    r, t, p, clipping=True, phase: Literal["water", "ice", "water+ice"] = "water"
):
    """Calculate relative humidity.

    Parameters
    ----------
    r : xarray.DataArray
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
        "water": {"shortName": "RELHUM"},
        "ice": {"shortName": "RH_ICE"},
        "water+ice": {"shortName": "RH_MIX_EC"},
    }

    if phase not in phase_conditions:
        raise ValueError("Invalid phase. Phase must be 'water', 'ice', or 'water+ice'.")

    q = r / (1 + r)

    pb, tb, qb = xr.broadcast(p, t, q)

    phase_for_svp = "mixed" if phase == "water+ice" else phase

    return xr.DataArray(
        data=(
            100
            * thermo.vapour_pressure_from_specific_humidity(qb, pb)
            / thermo.saturation_vapour_pressure(tb.values, phase=phase_for_svp)
        ).clip(0, max),
        attrs=metadata.override(
            t.metadata, shortName=phase_conditions[phase]["shortName"]
        ),
    )
