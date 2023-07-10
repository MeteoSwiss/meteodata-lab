"""algorithm for BRN operator."""
# Third-party
import numpy as np
import xarray as xr

# First-party
from idpi.operators.destagger import destagger
from idpi.operators.thetav import fthetav

pc_g = 9.80665


def fbrn(p, t, qv, u, v, hhl, hsurf):
    """Bulk Richardson Number (BRN)."""
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
        pc_g
        * (hfl - hsurf)
        * (thetav - thetav.isel(z=nlevels - 1))
        * nlevels_xr
        / (thetav_sum * (u_**2 + v_**2))
    )

    return brn
