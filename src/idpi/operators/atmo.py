"""Atmospheric thermodynamic functions."""

# Third-party
import numpy as np

# First-party
from idpi import physical_constants as pc


def pv_sw(t):
    """Pressure of water vapor at equilibrium over liquid water.

    Parameters
    ----------
    t : xr.DataArray
        temperature (in Kelvin)

    Returns
    -------
    xr.DataArray
        pressure of water vapor in Pascal

    """
    return pc.b1 * np.exp(pc.b2w * (t - pc.b3) / (t - pc.b4w))


def qv_pvp(pv, p):
    """Specific water vapor content (from perfect gas law and approximating q~w).

    Parameters
    ----------
    pv : xr.DataArray
        pressure of water vapor
    p : xr.DataArray
        pressure

    Returns
    -------
    xr.DataArray
        specific water vapor (dimensionless)

    """
    return pc.rdv * pv / np.maximum((p - pc.o_rdv * pv), 1.0)


def pv_qp(qv, p):
    """Partial pressure of water vapor (from perfect gas law and approximating q~w).

    Parameters
    ----------
    qv : xr.DataArray
        water vapor mixing ratio
    p : xr.DataArray
        pressure

    Returns
    -------
    xr.DataArray
        partial pressure of water vapor (same unit as p)

    """
    return qv * p / (pc.rdv + pc.o_rdv * qv)
