"""Algorithm to compute the density (rho)."""

# Third-party
import xarray as xr

# Local
from .. import constants as const


def f_rho_tot(
    T: xr.DataArray,
    P: xr.DataArray,
    QV: xr.DataArray,
    QC: xr.DataArray,
    QI: xr.DataArray | None = None,
    QP: xr.DataArray | None = None,
) -> xr.DataArray:
    """Total density of air mixture.

    Assumes perfect gas law, pressure as sum of partial pressures.
    Result is in [kg/m**3].

    Args:
        T (xr.DataArray): Temperature [Kelvin]
        P (xr.DataArray): Pressure [Pascal]
        QV (xr.DataArray): Specific humidity [kg/kg]
        QC (xr.DataArray): Specific cloud water content [kg/kg]
        QI (xr.DataArray, optional): Specific cloud ice content [kg/kg].
        QP (xr.DataArray, optional): Specific precipitable components content [kg/kg].

    """
    q = QC
    if QI is not None:
        q += QI
    if QP is not None:
        q += QP
    return P / (const.pc_r_d * T * (1.0 + const.pc_rvd_o * QV - q))
