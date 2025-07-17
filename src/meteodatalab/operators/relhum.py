"""Relative humidity operators."""

# Standard library
from typing import Literal

# Third-party
import xarray as xr
from earthkit.meteo import thermo  # type: ignore

# Local
from .. import metadata


def relhum(
    w, t, p, clipping=True, phase: Literal["water", "ice", "water+ice"] = "water"
):
    """Calculate relative humidity.

    Parameters
    ----------
    w : xarray.DataArray
        water vapor mixing ratio in kg/kg
    t : xarray.DataArray
        temperature in Kelvin
    p : xarray.DataArray
        pressure in Pa
    clipping : bool
        clips the relative humidity to [0,100] interval.
        Only upper bound is controlled by this parameter,
        since lower bound clipping is always performed.
    phase : Literal["water", "ice", "water+ice"]
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

    # Phase-specific metadata and saturation vapor pressure configuration
    phase_conditions = {
        "water": {
            "shortName": "RELHUM",
            "svp_phase": "water",
        },
        "ice": {
            "shortName": "RH_ICE",
            "svp_phase": "ice",
        },
        "water+ice": {
            "shortName": "RH_MIX_EC",
            "svp_phase": "mixed",  # earthkit-meteo op. requires "mixed"
        },
    }

    if phase not in phase_conditions:
        raise ValueError("Invalid phase. Phase must be 'water', 'ice', or 'water+ice'.")

    # Convert mixing ratio (w) to specific humidity (q)
    q = w / (1 + w)

    pb, tb, qb = xr.broadcast(p, t, q)

    # Use the mapped saturation vapor pressure phase
    svp_phase = phase_conditions[phase]["svp_phase"]

    # Compute relative humidity using earthkit-meteo operators
    rh = (
        100
        * thermo.vapour_pressure_from_specific_humidity(qb, pb)
        / thermo.saturation_vapour_pressure(tb.values, phase=svp_phase)
    ).clip(0, max)

    # Return RH with appropriate metadata
    return xr.DataArray(
        data=rh,
        attrs=metadata.override(
            t.metadata, shortName=phase_conditions[phase]["shortName"]
        ),
    )
