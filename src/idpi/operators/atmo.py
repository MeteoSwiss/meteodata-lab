"""Atmospheric thermodynamic functions."""
# Third-party
import numpy as np

# First-party
from idpi.constants import pc_b1, pc_b2w, pc_b3, pc_b4w, pc_o_rdv, pc_rdv


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
    return pc_b1 * np.exp(pc_b2w * (t - pc_b3) / (t - pc_b4w))


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
    return pc_rdv * pv / np.maximum((p - pc_o_rdv * pv), 1.0)


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
    return qv * p / (pc_rdv + pc_o_rdv * qv)
