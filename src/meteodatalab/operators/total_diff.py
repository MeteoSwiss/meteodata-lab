"""Finite difference stencils on xarray dataarrays."""

# Standard library
import dataclasses as dc

# Third-party
import numpy as np
import xarray as xr

# Local
from . import diff
from .destagger import destagger


@dc.dataclass
class TotalDiff:
    """Diff operators for terrain following grid."""

    dlon: float
    dlat: float
    sqrtg_r_s: xr.DataArray
    dzeta_dlam: xr.DataArray
    dzeta_dphi: xr.DataArray

    @classmethod
    def from_hhl(cls, hhl: xr.DataArray):
        deg2rad = np.pi / 180
        dlon = hhl.geography["iDirectionIncrementInDegrees"] * deg2rad
        dlat = hhl.geography["jDirectionIncrementInDegrees"] * deg2rad

        dh_dx = destagger(diff.dx(hhl), "z")  # order is important
        dh_dy = destagger(diff.dy(hhl), "z")  # diff then destagger
        dh_dz = diff.dz_staggered(hhl)

        sqrtg_r_s = -1 / dh_dz
        dzeta_dlam = sqrtg_r_s / dlon * dh_dx
        dzeta_dphi = sqrtg_r_s / dlat * dh_dy

        return cls(dlon, dlat, sqrtg_r_s, dzeta_dlam, dzeta_dphi)

    def d_dlam(self, df_dx: xr.DataArray, df_dz: xr.DataArray) -> xr.DataArray:
        """Compute the derivative along the lambda axis."""
        return df_dx / self.dlon + df_dz * self.dzeta_dlam

    def d_dphi(self, df_dy: xr.DataArray, df_dz: xr.DataArray) -> xr.DataArray:
        """Compute the derivative along the phi axis."""
        return df_dy / self.dlat + df_dz * self.dzeta_dphi

    def d_dzeta(self, df_dz: xr.DataArray) -> xr.DataArray:
        """Compute the derivative along the zeta axis."""
        return df_dz * self.sqrtg_r_s
