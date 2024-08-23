"""ICON native grid helper functions."""

# Standard library
from pathlib import Path
from uuid import UUID
from typing import Literal

# Third-party
import numpy as np
import xarray as xr

GRID_ID = {
    "icon-ch1-eps": UUID("17643da2-5749-59b6-44d2-54a3cd6e2bc0"),
    "icon-ch2-eps": UUID("bbbd5a09-8554-9924-3c7a-4aa4c8762920"),
}
GRID_DIR = Path("/scratch/mch/jenkins/icon/pool/data/ICON/mch/grids/")
GRID_MAP = {
    GRID_ID["icon-ch1-eps"]: GRID_DIR / "icon-1/icon_grid_0001_R19B08_mch.nc",
    GRID_ID["icon-ch2-eps"]: GRID_DIR / "icon-2/icon_grid_0002_R19B07_mch.nc",
}


def get_icon_grid(grid_uuid: str) -> dict[str, xr.DataArray]:
    """Get ICON native grid coordinates.

    Parameters
    ----------
    grid_uuid : str
        The UUID of the horizontal grid.

    Raises
    ------
    KeyError
        If the UUID is not found in the GRID_MAP constant.

    Returns
    -------
    dict[str, xarray.DataArray]
        Geodectic coordinates of the ICON grid cell centers.

    """
    grid_path = GRID_MAP.get(UUID(grid_uuid))

    if grid_path is None:
        raise KeyError

    ds = xr.open_dataset(grid_path)

    rad2deg = 180 / np.pi
    result = ds[["clon", "clat"]].reset_coords() * rad2deg
    return {"lon": result.clon, "lat": result.clat}


def get_remap_coeffs(
    grid_uuid: str, grid_type: Literal["rotlatlon", "geolatlon"]
) -> xr.Dataset:
    """Get ICON native grid remap indices and weights.

    Parameters
    ----------
    grid_uuid : str
        The UUID of the horizontal grid in hex format.

    Raises
    ------
    KeyError
        If the UUID is not found in the GRID_ID constant.

    Returns
    -------
    xarray.Dataset
        Dataset of the remap indices and weights.

    """
    model = {v.hex: k for k, v in GRID_ID.items()}[grid_uuid]
    coeffs_path = (
        f"/store_new/mch/msopr/icon_workflow_2/iconremap-weights/{model}-{grid_type}.nc"
    )
    return xr.open_dataset(coeffs_path)
