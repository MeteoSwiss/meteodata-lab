"""Algorithm for the curl operator."""

# Standard library
from typing import cast

# Third-party
import numpy as np
import xarray as xr

# Local
from .. import constants as const
from . import diff
from .destagger import destagger
from .total_diff import TotalDiff


def curl(
    u: xr.DataArray,
    v: xr.DataArray,
    w: xr.DataArray,
    rlat: xr.DataArray,
    total_diff: TotalDiff,
) -> tuple[xr.DataArray, xr.DataArray, xr.DataArray]:
    """Compute the curl of the velocity field."""
    r_earth_inv = 1 / const.earth_radius
    acrlat = cast(xr.DataArray, 1 / (np.cos(rlat) * const.earth_radius))
    tgrlat = cast(xr.DataArray, np.tan(rlat))

    # compute weighted derivatives for FD
    u_f = destagger(u, "x")
    v_f = destagger(v, "y")
    w_f = destagger(w, "generalVertical")

    du_dz = diff.dz(u_f)
    du_dphi = total_diff.d_dphi(diff.dy(u_f), du_dz)
    du_dzeta = total_diff.d_dzeta(du_dz)

    dv_dz = diff.dz(v_f)
    dv_dlam = total_diff.d_dlam(diff.dx(v_f), dv_dz)
    dv_dzeta = total_diff.d_dzeta(dv_dz)

    dw_dz = diff.dz_staggered(w)
    dw_dlam = total_diff.d_dlam(diff.dx(w_f), dw_dz)
    dw_dphi = total_diff.d_dphi(diff.dy(w_f), dw_dz)

    # compute curl
    curl1 = acrlat * (r_earth_inv * dw_dphi + dv_dzeta - r_earth_inv * v_f)
    curl2 = r_earth_inv * (-du_dzeta - acrlat * dw_dlam + r_earth_inv * u_f)
    curl3 = acrlat * dv_dlam + r_earth_inv * (-du_dphi + tgrlat * u_f)

    return curl1, curl2, curl3


def curl_alt(
    u: xr.DataArray,
    v: xr.DataArray,
    w: xr.DataArray,
    rlat: xr.DataArray,
    total_diff: TotalDiff,
) -> tuple[xr.DataArray, xr.DataArray, xr.DataArray]:
    td = total_diff

    r_earth_inv = 1 / const.earth_radius
    acrlat = 1 / (np.cos(rlat) * const.earth_radius)
    tgrlat = np.tan(rlat)

    u_f = destagger(u, "x")
    v_f = destagger(v, "y")
    w_f = destagger(w, "generalVertical")

    du_dphi = np.gradient(u_f, td.dlat, axis=-2)
    du_dzeta = np.gradient(u_f, axis=-3)

    dv_dlam = np.gradient(v_f, td.dlon, axis=-1)
    dv_dzeta = np.gradient(v_f, axis=-3)

    dw_dlam = np.gradient(w_f, td.dlon, axis=-1)
    dw_dphi = np.gradient(w_f, td.dlat, axis=-2)
    dw_dzeta = np.diff(w, axis=-3)

    curl1 = acrlat * (
        r_earth_inv * (dw_dphi + td.dzeta_dphi * dw_dzeta)
        + td.sqrtg_r_s * dv_dzeta
        - r_earth_inv * v_f
    )
    curl2 = r_earth_inv * (
        -td.sqrtg_r_s * du_dzeta
        - acrlat * (dw_dlam + td.dzeta_dlam * dw_dzeta)
        + r_earth_inv * u_f
    )
    curl3 = (
        acrlat * (dv_dlam + td.dzeta_dlam * dv_dzeta)
        - r_earth_inv * (du_dphi + td.dzeta_dphi * du_dzeta)
        + r_earth_inv * tgrlat * u_f
    )

    return curl1, curl2, curl3
