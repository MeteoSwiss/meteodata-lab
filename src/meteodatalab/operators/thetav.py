"""Definition of the thetav operator."""

# Third-party
import xarray as xr
from earthkit.meteo import thermo  # type: ignore

# Local
from .. import metadata


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
    result = xr.apply_ufunc(thermo.virtual_potential_temperature, t, qv, p)
    return result.assign_attrs(metadata.override(t.metadata, shortName="THETA_V"))
