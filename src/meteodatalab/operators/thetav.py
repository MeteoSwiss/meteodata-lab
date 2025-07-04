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
    pb, tb, qvb = xr.broadcast(p, t, qv)

    return xr.DataArray(
        data=thermo.virtual_potential_temperature(tb.values, qvb.values, pb.values),
        dims=pb.dims,
        attrs=metadata.override(t.metadata, shortName="THETA_V"),
    )
