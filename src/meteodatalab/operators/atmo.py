"""Atmospheric thermodynamic functions."""

# Third-party
import numpy as np

# First-party
from meteodatalab import physical_constants as pc


def pv_sw(t):
    """Pressure of water vapor at equilibrium over liquid water.

    Parameters
    ----------
    t : xarray.DataArray
        temperature (in Kelvin)

    Returns
    -------
    xarray.DataArray
        pressure of water vapor in Pascal

    """
    return pc.b1 * np.exp(pc.b2w * (t - pc.b3) / (t - pc.b4w))


def pv_si(t):
    """Pressure of water vapor at equilibrium over ice.

    Parameters
    ----------
    t : xarray.DataArray
        temperature (in Kelvin)

    Returns
    -------
    xarray.DataArray
        pressure of water vapor in Pascal

    """
    return pc.b1 * np.exp(pc.b2i * (t - pc.b3) / (t - pc.b4i))


def pv_sm(t):
    """Pressure of water vapor at equilibrium over mixed phase.

    Parameters
    ----------
    t : xarray.DataArray
        temperature (in Kelvin)

    Returns
    -------
    xarray.DataArray
        pressure of water vapor in Pascal

    """
    tice_only = pc.b3 - 23
    dtice = pc.b3 - tice_only
    alpha = ((t - tice_only) / dtice) ** 2
    water = pv_sw(t)
    ice = pv_si(t)
    mix = alpha * water + (1.0 - alpha) * ice
    pv_sm = water.where(t > pc.b3, ice.where(t < tice_only, mix))
    return pv_sm


def qv_pvp(pv, p):
    """Specific water vapor content (from perfect gas law and approximating q~w).

    Parameters
    ----------
    pv : xarray.DataArray
        pressure of water vapor
    p : xarray.DataArray
        pressure

    Returns
    -------
    xarray.DataArray
        specific water vapor (dimensionless)

    """
    return pc.rdv * pv / np.maximum((p - pc.o_rdv * pv), 1.0)


def pv_qp(qv, p):
    """Partial pressure of water vapor (from perfect gas law and approximating q~w).

    Parameters
    ----------
    qv : xarray.DataArray
        water vapor mixing ratio
    p : xarray.DataArray
        pressure

    Returns
    -------
    xarray.DataArray
        partial pressure of water vapor (same unit as p)

    """
    return qv * p / (pc.rdv + pc.o_rdv * qv)
