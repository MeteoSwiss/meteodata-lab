"""Finite difference stencils on xarray dataarrays."""
# Standard library
import dataclasses as dc
from typing import Final

# Third-party
import xarray as xr

# Local
from . import diff
from .destagger import destagger


@dc.dataclass
class TotalDiff:
    """Diff operators for terrain following grid."""

    dlon: float
    dlat: float
    hhl: dc.InitVar[xr.DataArray]
    sqrtg_r_s: xr.DataArray = dc.field(init=False)
    dzeta_dlam: xr.DataArray = dc.field(init=False)
    dzeta_dphi: xr.DataArray = dc.field(init=False)

    def __post_init__(self, hhl: xr.DataArray):
        z: Final = "generalVertical"
        dh_dx = destagger(diff.dx(hhl), z)  # order is important
        dh_dy = destagger(diff.dy(hhl), z)  # diff then destagger
        dh_dz = diff.dz_staggered(hhl)

        self.sqrtg_r_s = -1 / dh_dz
        self.dzeta_dlam = self.sqrtg_r_s / self.dlon * dh_dx
        self.dzeta_dphi = self.sqrtg_r_s / self.dlat * dh_dy

    def d_dlam(self, df_dx: xr.DataArray, df_dz: xr.DataArray) -> xr.DataArray:
        """Compute the derivative along the lambda axis."""
        return df_dx / self.dlon + df_dz * self.dzeta_dlam

    def d_dphi(self, df_dy: xr.DataArray, df_dz: xr.DataArray) -> xr.DataArray:
        """Compute the derivative along the phi axis."""
        return df_dy / self.dlat + df_dz * self.dzeta_dphi

    def d_dzeta(self, df_dz: xr.DataArray) -> xr.DataArray:
        """Compute the derivative along the zeta axis."""
        return df_dz * self.sqrtg_r_s
