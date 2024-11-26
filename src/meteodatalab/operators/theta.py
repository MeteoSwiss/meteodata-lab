"""algorithm to compute the potential temperature theta in K."""

# Third-party
import xarray as xr

# Local
from .. import metadata
from .. import physical_constants as pc


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
    # Reference surface pressure for computation of potential temperature
    p0 = 1.0e5

    return xr.DataArray(
        data=(p0 / p) ** pc.rdocp * t,
        attrs=metadata.override(p.metadata, shortName="PT"),
    )
