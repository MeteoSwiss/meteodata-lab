"""ICON native grid helper functions."""

# Standard library
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Literal
from uuid import UUID

# Third-party
import numpy as np
import xarray as xr

GRID_UUID_TO_MODEL = {
    UUID("17643da2-5749-59b6-44d2-54a3cd6e2bc0"): "icon-ch1-eps",
    UUID("bbbd5a09-8554-9924-3c7a-4aa4c8762920"): "icon-ch2-eps",
}


def load_grid_from_file(
    uuid: UUID, grid_paths: dict[UUID, Path]
) -> dict[str, xr.DataArray]:
    """Load the clat and clon grid coordinates from .nc format file.

    Parameters
    ----------
    uuid: UUID
        The UUID of the horizontal grid as specified in the GRIB metadata.
    grid_paths: dict[UUID, Path]
        Dictionary mapping from horizontal grid UUID to the path where the data file is.

    Raises
    ------
    KeyError
        If the UUID does not match a known model.

    Returns
    -------
    dict[str, xr.DataArray]
        Dataset containing clon and clat coordinates of the ICON grid cell centers for
        the model.

    """
    grid_path = grid_paths.get(uuid)
    if grid_path is None:
        raise KeyError(
            "No grid file for UUID %s. Known UUIDs are %s.", uuid, grid_paths.keys()
        )
    rad2deg = 180 / np.pi
    ds = xr.open_dataset(grid_path)
    result = ds[["clon", "clat"]].reset_coords() * rad2deg
    return {"lon": result.clon, "lat": result.clat}


def load_boundary_idx_from_file(uuid: UUID) -> xr.DataArray:
    """Load the lateral boundary strip index from .nc format file.

    Parameters
    ----------
    uuid: UUID
        The UUID of the horizontal grid as specified in the GRIB metadata.

    Returns
    -------
    xr.DataArray
        Lateral boundary strip index for the given grid.

    """
    grid_dir = Path("/scratch/mch/jenkins/icon/pool/data/ICON/mch/grids/")
    grid_paths = {
        UUID("17643da2-5749-59b6-44d2-54a3cd6e2bc0"): grid_dir
        / "icon-1/icon_grid_0001_R19B08_mch.nc",
        UUID("bbbd5a09-8554-9924-3c7a-4aa4c8762920"): grid_dir
        / "icon-2/icon_grid_0002_R19B07_mch.nc",
    }
    grid_path = grid_paths.get(uuid)
    if grid_path is None:
        raise KeyError(
            "No grid file for UUID %s. Known UUIDs are %s.", uuid, grid_paths.keys()
        )
    ds = xr.open_dataset(grid_path)
    return ds["refin_c_ctrl"].assign_attrs(
        uuidOfHGrid=ds.attrs["uuidOfHGrid"],
    )


def load_grid_from_balfrin() -> Callable[[UUID], dict[str, xr.DataArray]]:
    """Return a grid source to load grid files when running on balfrin."""
    grid_dir = Path("/scratch/mch/jenkins/icon/pool/data/ICON/mch/grids/")
    grid_paths = {
        UUID("17643da2-5749-59b6-44d2-54a3cd6e2bc0"): grid_dir
        / "icon-1/icon_grid_0001_R19B08_mch.nc",
        UUID("bbbd5a09-8554-9924-3c7a-4aa4c8762920"): grid_dir
        / "icon-2/icon_grid_0002_R19B07_mch.nc",
    }
    return partial(load_grid_from_file, grid_paths=grid_paths)


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
    model = GRID_UUID_TO_MODEL[UUID(grid_uuid)]
    coeffs_path = (
        f"/store_new/mch/msopr/icon_workflow_2/iconremap-weights/{model}-{grid_type}.nc"
    )
    return xr.open_dataset(coeffs_path)
