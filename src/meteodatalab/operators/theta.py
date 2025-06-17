"""algorithm to compute the potential temperature theta in K."""

# Third-party
import xarray as xr
from earthkit.meteo import thermo # type: ignore

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

    Returns
    -------
    xarray.DataArray
        potential temperature in K

    """

    return xr.DataArray(
        thermo.potential_temperature(t.values, p.values),
        attrs=metadata.override(p.metadata, shortName="PT"),
    )
