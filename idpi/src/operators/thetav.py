#!/usr/bin/python


def fthetav(p, t, qv):
    """Virtual potential temperature in K.

    Parameters
    ----------
        p : xarray.DataArray
            pressure in Pa
        t : xarray.DataArray
            air temperature in K
        qv: xarray.DataArray
            specific humidity (dimensionless)

    Returns
    -------
        thetav: xarray.DataArray
            virtual potential temperature in K
    """
    # Physical constants
    pc_r_d = 287.05  # Gas constant for dry air [J kg-1 K-1]
    pc_r_v = 461.51  # Gas constant for water vapour[J kg-1 K-1]
    pc_cp_d = 1005.0  # Specific heat capacity of dry air at 0 deg C and constant pressure [J kg-1 K-1]

    # Derived quantities
    pc_rvd = pc_r_v / pc_r_d
    pc_rdocp = pc_r_d / pc_cp_d
    pc_rvd_o = pc_rvd - 1.0

    # Reference surface pressure for computation of potential temperature
    p0 = 1.0e5

    return (p0 / p) ** pc_rdocp * t * (1.0 + (pc_rvd_o * qv / (1.0 - qv)))
