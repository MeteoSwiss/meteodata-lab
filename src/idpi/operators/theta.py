"""algorithm to compute the potential temperature theta in K."""
# Third-party
import xarray as xr

# Local
from .. import physical_constants as pc


def ftheta(p: xr.DataArray, t: xr.DataArray) -> xr.DataArray:
    """Potential temperature in K.

    Args:
        p (xr.DataArray): pressure in Pa
        t (xr.DataArray): air temperature in K

    Returns:
        xr.DataArray: potential temperature in K

    """
    # Reference surface pressure for computation of potential temperature
    p0 = 1.0e5

    result = (p0 / p) ** pc.rdocp * t
    result.attrs = p.attrs | {"parameter": None}

    return result
