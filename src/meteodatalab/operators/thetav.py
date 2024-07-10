"""Definition of the thetav operator."""

# Third-party
import xarray as xr

# Local
from .. import metadata
from .. import physical_constants as pc


def fthetav(p: xr.DataArray, t: xr.DataArray, qv: xr.DataArray) -> xr.DataArray:
    """Virtual potential temperature in K.

    Parameters
    ----------
    p : xarray.DataArray
        pressure in Pa
    t : xarray.DataArray
        air temperature in K
    qv : xarray.DataArray
        specific humidity (dimensionless)

    Returns
    -------
    xarray.DataArray
        virtual potential temperature in K

    """
    # Reference surface pressure for computation of potential temperature
    p0 = 1.0e5

    return xr.DataArray(
        data=(p0 / p) ** pc.rdocp * t * (1.0 + (pc.rvd_o * qv / (1.0 - qv))),
        attrs=metadata.override(t.message, shortName="THETA_V"),
    )
