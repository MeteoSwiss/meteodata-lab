"""Radiation related operators."""

# Third-party
import xarray as xr

# Local
from .. import metadata
from .. import physical_constants as pc


def compute_athd_s(athb_s: xr.DataArray, tsurf: xr.DataArray) -> xr.DataArray:
    """Compute incoming longwave radiation at surface level.

    Parameters
    ----------
    athb_s : xarray.DataArray
        Net long-wave radiation flux at surface [W m-2]
    tsurf : xarray.DataArray
        Temperature at surface [K]

    Returns
    -------
    xarray.DataArray
        Average downward longwave radiation at the surface [W m-2]

    """
    return xr.DataArray(
        data=athb_s / pc.emissivity_surface + pc.boltzman_cst * tsurf**4,
        attrs=metadata.override(athb_s.metadata, shortName="ATHD_S"),
    )


def compute_swdown(diffuse: xr.DataArray, direct: xr.DataArray) -> xr.DataArray:
    """Compute downward shortwave radiation.

    Parameters
    ----------
    diffuse : xarray.DataArray
        incoming diffuse shortwave radiation.
    direct : xarray.DataArray
        incoming direct shortwave radiation.

    Returns
    -------
    xarray.DataArray
        downward shortwave radiation at surface level.

    """
    return xr.DataArray(
        data=(diffuse + direct).clip(min=0),
        attrs=metadata.override(diffuse.metadata, shortName="ASOD_S"),
    )
