"""Algorithm to compute the density (rho)."""

# Third-party
import xarray as xr

# Local
from .. import physical_constants as pc


def compute_rho_tot(
    t: xr.DataArray,
    p: xr.DataArray,
    qv: xr.DataArray,
    qc: xr.DataArray,
    qi: xr.DataArray | None = None,
    qp: xr.DataArray | None = None,
) -> xr.DataArray:
    """Total density of air mixture.

    Assumes perfect gas law, pressure as sum of partial pressures.

    Parameters
    ----------
    t : xarray.DataArray
        Temperature [Kelvin]
    p : xarray.DataArray
        Pressure [Pascal]
    qv : xarray.DataArray
        Specific humidity [kg/kg]
    qc : xarray.DataArray
        Specific cloud water content [kg/kg]
    qi : xarray.DataArray, optional
        Specific cloud ice content [kg/kg]
    qp : xarray.DataArray, optional
        Specific precipitable components content [kg/kg]

    Returns
    -------
    xarray.DataArray
        Total density of air mixture [kg/m**3]

    """
    q = qc
    if qi is not None:
        q += qi
    if qp is not None:
        q += qp

    return p / (pc.r_d * t * (1.0 + pc.rvd_o * qv - q))
