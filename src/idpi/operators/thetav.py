"""Definition of the thetav operator."""

# Local
from .. import physical_constants as pc


def fthetav(p, t, qv):
    """Virtual potential temperature in K.

    Arguments
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
    # Reference surface pressure for computation of potential temperature
    p0 = 1.0e5

    return (p0 / p) ** pc.rdocp * t * (1.0 + (pc.rvd_o * qv / (1.0 - qv)))
