#!/usr/bin/python
import numpy as np
import xarray as xr
from operators.thetav import fthetav

pc_g = 9.80665


def fbrn(p, t, qv, u, v, hhl, hsurf):
    nlevels = len(p.coords["generalVerticalLayer"])

    thetav = fthetav(p, t, qv)
    thetav_sum = thetav.isel(generalVerticalLayer=slice(None, None, -1)).\
        cumsum(
        dim="generalVerticalLayer"
    )

    nlevels_xr = xr.DataArray(
        data=np.arange(nlevels, 0, -1), dims=["generalVerticalLayer"]
    )

    brn = (
        pc_g
        * (hhl - hsurf)
        * (thetav - thetav.isel(generalVerticalLayer=79))
        / ((thetav_sum / nlevels_xr) * (u ** 2 + v ** 2))
    )
    return brn
