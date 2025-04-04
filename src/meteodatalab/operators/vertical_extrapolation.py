"""Vertical extrapolation operators."""

# Third-party
import numpy as np
import xarray as xr

G = 9.80665  # m/s^2
R_d = 287.053  # Pa K^-1 m^3 kg^-1
LAPSE_RATE = 0.0065  # K m^-1
T1 = 2000.0
T2 = 2500.0


def extrapolate_temperature_sfc2p(
    t_sfc: xr.DataArray,
    z_sfc: xr.DataArray,
    p_sfc: xr.DataArray,
    p_target: float,
) -> xr.DataArray:
    """Extrapolate temperature to a target pressure level.

    Implements the algorithm described in [1]_.

    Parameters
    ----------
    t_sfc : xr.DataArray
        Surface temperature.
    z_sfc : xr.DataArray
        Surface geopotential.
    p_sfc : xr.DataArray
        Surface pressure.
    p_target : float
        Target pressure level.

    Returns
    -------
    xr.DataArray
        Extrapolated temperature at the target pressure level.

    References
    ----------
    .. [1] https://www.umr-cnrm.fr/gmapdoc/IMG/pdf/ykfpos46t1r1.pdf

    """
    y = _vertical_extrapolation_y_term(t_sfc, p_sfc, z_sfc, p_target)
    return t_sfc * (1 + y + (y**2) / 2 + (y**3) / 6)


def extrapolate_geopotential_sfc2p(
    z_sfc: xr.DataArray,
    t_sfc: xr.DataArray,
    p_sfc: xr.DataArray,
    p_target: float,
) -> xr.DataArray:
    """Extrapolate geopotential to a target pressure level.

    Implements the algorithm described in [1]_.

    Parameters
    ----------
    z_sfc : xr.DataArray
        Surface geopotential.
    t_sfc : xr.DataArray
        Surface temperature.
    p_sfc : xr.DataArray
        Surface pressure.
    p_target : float
        Target pressure level.

    Returns
    -------
    xr.DataArray
        Extrapolated geopotential at the target pressure level.

    References
    ----------
    .. [1] https://www.umr-cnrm.fr/gmapdoc/IMG/pdf/ykfpos46t1r1.pdf

    """
    y = _vertical_extrapolation_y_term(
        t_sfc, p_sfc, z_sfc, p_target, lapse_rate=LAPSE_RATE
    )
    return z_sfc - R_d * t_sfc * np.log(p_target / p_sfc) * (1 + y / 2 + (y**2) / 6)


def _vertical_extrapolation_t_zero_prime(t_sfc, z_sfc):
    t = t_sfc + LAPSE_RATE * z_sfc / G
    t_min = np.minimum(t, 298.0)
    return xr.where(z_sfc / G > T2, t_min, t_min * 0.5 + t * 0.5)


def _vertical_extrapolation_lapse_rate(z_sfc, t_sfc):
    t_zero_prime = _vertical_extrapolation_t_zero_prime(t_sfc, z_sfc)
    return xr.where(
        z_sfc / G < T1, LAPSE_RATE, G / z_sfc * np.maximum(t_zero_prime - t_sfc, 0.0)
    )


def _vertical_extrapolation_y_term(t_sfc, p_sfc, z_sfc, p_target, lapse_rate=None):
    if lapse_rate is None:
        lapse_rate = _vertical_extrapolation_lapse_rate(z_sfc, t_sfc)
    return lapse_rate * R_d / G * np.log(p_target / p_sfc)
