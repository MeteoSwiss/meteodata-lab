"""algorithm to compute the potential temperature theta in K."""


def ftheta(p, t):
    """Potential temperature in K.

    Parameters
    ----------
        p : xarray.DataArray
            pressure in Pa
        t : xarray.DataArray
            air temperature in K

    Returns
    -------
        theta: xarray.DataArray
            potential temperature in K
    """
    # Physical constants
    pc_r_d = 287.05  # Gas constant for dry air [J kg-1 K-1]
    pc_cp_d = 1005.0  # Specific heat capacity of dry air at 0 deg C and constant pressure [J kg-1 K-1]
    pc_rdocp = pc_r_d / pc_cp_d

    # Reference surface pressure for computation of potential temperature
    p0 = 1.0e5

    return (p0 / p) ** pc_rdocp * t
