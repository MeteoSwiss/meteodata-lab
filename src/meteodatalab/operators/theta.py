"""algorithm to compute the potential temperature theta in K."""

# Third-party
import xarray as xr
from earthkit.meteo import thermo  # type: ignore

# Local
from .. import metadata


def compute_theta(p: xr.DataArray, t: xr.DataArray) -> xr.DataArray:
    """Potential temperature in K.

    Parameters
    ----------
    p : xarray.DataArray
        pressure in Pa
    t : xarray.DataArray
        air temperature in K

    Constants
    ---------
    Reference surface pressure for computation of potential temperature
    p0 = 1.0e5

    Returns
    -------
    xarray.DataArray
        potential temperature in K

    """
    return xr.DataArray(
        thermo.potential_temperature(t.values, p.values),
        dims=p.dims,
        attrs=metadata.override(p.metadata, shortName="PT"),
    )
