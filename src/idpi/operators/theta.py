"""algorithm to compute the potential temperature theta in K."""
# Third-party
import xarray as xr


def ftheta(p: xr.DataArray, t: xr.DataArray) -> xr.DataArray:
    """Potential temperature in K.

    Args:
        p (xr.DataArray): pressure in Pa
        t (xr.DataArray): air temperature in K

    Returns:
        xr.DataArray: potential temperature in K

    """
    # Physical constants
    pc_r_d = 287.05  # Gas constant for dry air [J kg-1 K-1]
    # Specific heat capacity of dry air at 0 deg C with
    # constant pressure [J kg-1 K-1]
    pc_cp_d = 1005.0
    pc_rdocp = pc_r_d / pc_cp_d

    # Reference surface pressure for computation of potential temperature
    p0 = 1.0e5

    result = (p0 / p) ** pc_rdocp * t
    result.attrs = p.attrs | {"parameter": None}

    return result
