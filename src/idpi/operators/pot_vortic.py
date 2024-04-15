"""Implementation of the potential vorticity operator."""

# Third-party
import numpy as np
import xarray as xr

# Local
from .. import metadata
from .. import physical_constants as pc
from . import diff
from .curl import curl
from .gis import get_grid
from .total_diff import TotalDiff


def compute_pot_vortic(
    u: xr.DataArray,
    v: xr.DataArray,
    w: xr.DataArray,
    theta: xr.DataArray,
    rho_tot: xr.DataArray,
    hhl: xr.DataArray,
) -> xr.DataArray:
    r"""Compute the potential vorticity.

    The potential vorticity is computed with the following formula:

    .. math::
        v_p = \frac{1}{\rho} * \frac{\partial \Theta}{\partial \z} * (c_v + 2 \Omega)

    where
    :math:`\rho` is the total air density,
    :math:`\frac{\partial \Theta}{\partial \z}`
    is the vertical gradient of the potential temperature,
    :math:`c_v` is the curl of the wind in y direction and
    :math`\Omega` is the coriolis term.

    Parameters
    ----------
    u : xarray.DataArray
        Wind in x direction [m/s]
    v : xarray.DataArray
        Wind in y direction [m/s]
    w : xarray.DataArray
        Wind in z direction [m/s]
    theta : xarray.DataArray
        Potential Temperature [K]
    rho_tot : xarray.DataArray
        Total density [kg m-3]
    hhl : xarray.DataArray
        Height at half levels [m]

    Returns
    -------
    xarray.DataArray
        The potential vorticity

    """
    # target coordinates
    deg2rad = np.pi / 180
    lat = (hhl.lat * deg2rad).astype(np.float32)

    rlat = get_grid(hhl.geography).rlat * deg2rad
    total_diff = TotalDiff.from_hhl(hhl)

    # compute curl
    curl1, curl2, curl3 = curl(u, v, w, rlat, total_diff)

    # coriolis terms
    cor2 = 2 * pc.omega / pc.earth_radius * np.cos(lat)
    cor3 = 2 * pc.omega * np.sin(lat)

    dt_dlam = total_diff.d_dlam(diff.dx(theta), diff.dz(theta))
    dt_dphi = total_diff.d_dphi(diff.dy(theta), diff.dz(theta))
    dt_dzeta = total_diff.d_dzeta(diff.dz(theta))

    # potential vorticity
    out = (
        dt_dlam * curl1 + dt_dphi * (curl2 + cor2) - dt_dzeta * (curl3 + cor3)
    ) / rho_tot

    out.attrs = metadata.override(theta.message, shortName="POT_VORTIC")

    return out
