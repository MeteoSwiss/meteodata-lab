"""algorithm for BRN operator."""

# Third-party
import numpy as np
import xarray as xr

# Local
from .. import metadata
from .. import physical_constants as pc
from .destagger import destagger
from .thetav import fthetav


def fbrn(
    p: xr.DataArray,
    t: xr.DataArray,
    qv: xr.DataArray,
    u: xr.DataArray,
    v: xr.DataArray,
    hhl: xr.DataArray,
    hsurf: xr.DataArray,
) -> xr.DataArray:
    """Bulk Richardson Number (BRN).

    Parameters
    ----------
    p : xarray.DataArray
        pressure in Pa
    t : xarray.DataArray
        air temperature in K
    qv : xarray.DataArray
        specific humidity (dimensionless)
    u : xarray.DataArray
        the x component of the wind velocity in m/s
    v : xarray.DataArray
        the y component of the wind velocity in m/s
    hhl : xarray.DataArray
        Heights of the interfaces between vertical layers in m amsl
    hsurf : xarray.DataArray
        earth surface height in m amsl


    Returns
    -------
    xarray.DataArray
        Bulk Richardson Number (dimensionless)

    """
    nlevels = p.sizes["z"]

    thetav = fthetav(p, t, qv)
    thetav_sum = (
        thetav.isel(z=slice(None, None, -1))
        .cumsum(dim="z")
        .isel(z=slice(None, None, -1))
    )

    nlevels_xr = xr.DataArray(data=np.arange(nlevels, 0, -1), dims=["z"])
    u_ = destagger(u, "x")
    v_ = destagger(v, "y")
    hfl = destagger(hhl, "z")

    brn = (
        pc.g
        * (hfl - hsurf)
        * (thetav - thetav.isel(z=nlevels - 1))
        * nlevels_xr
        / (thetav_sum * (u_**2 + v_**2))
    )

    return xr.DataArray(
        data=brn,
        attrs=metadata.override(p.metadata, shortName="BRN"),
    )
