"""ICON native grid helper functions."""

# Standard library
from pathlib import Path
from typing import Literal
from uuid import UUID

# Third-party
import numpy as np
import xarray as xr

GRID_ID = {
    "icon-ch1-eps": UUID("17643da2-5749-59b6-44d2-54a3cd6e2bc0"),
    "icon-ch2-eps": UUID("bbbd5a09-8554-9924-3c7a-4aa4c8762920"),
}


def get_remap_coeffs(
    grid_uuid: str, grid_type: Literal["rotlatlon", "geolatlon"]
) -> xr.Dataset:
    """Get ICON native grid remap indices and weights.

    Parameters
    ----------
    grid_uuid : str
        The UUID of the horizontal grid in hex format.
    grid_type : str
        Type of grid to remap to.

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
