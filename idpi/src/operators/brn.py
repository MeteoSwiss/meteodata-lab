"""algorithm for BRN operator."""
import numpy as np
import xarray as xr
from operators.thetav import fthetav

pc_g = 9.80665


def fbrn(p, t, qv, u, v, hhl, hsurf):
    """Compute the Bulk Richardson Number (BRN)."""
    nlevels = len(p.coords["generalVerticalLayer"])

    thetav = fthetav(p, t, qv)
    thetav_sum = thetav.isel(generalVerticalLayer=slice(None, None, -1)).cumsum(
        dim="generalVerticalLayer"
    )

    nlevels_xr = xr.DataArray(
        data=np.arange(nlevels, 0, -1), dims=["generalVerticalLayer"]
    )
    u_ = u
    v_ = v
    u_[dict(x=slice(1, None))] = (
        u.isel(x=slice(0, -1)) + u.isel(x=slice(1, None))
    ) * 0.5
    v_[dict(y=slice(1, None))] = (
        v.isel(y=slice(0, -1)) + v.isel(y=slice(1, None))
    ) * 0.5

    hhl_k0 = hhl[dict(generalVerticalLayer=slice(0, -1))].assign_coords(
        generalVerticalLayer=hhl[
            dict(generalVerticalLayer=slice(0, -1))
        ].generalVerticalLayer
    )

    hhl_k1 = hhl[dict(generalVerticalLayer=slice(1, None))].assign_coords(
        generalVerticalLayer=hhl[
            dict(generalVerticalLayer=slice(0, -1))
        ].generalVerticalLayer
    )

    hhl_fl = (hhl_k0 + hhl_k1) * 0.5

    brn = (
        pc_g
        * (hhl_fl - hsurf)
        * (thetav - thetav.isel(generalVerticalLayer=79))
        * nlevels_xr
        / (thetav_sum * (u_**2 + v_**2))
    )

    return brn
