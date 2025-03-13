"""ICON native grid helper functions."""

# Standard library
import dataclasses as dc
from abc import ABC, abstractmethod
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


class ICONGridSource(ABC):

    @abstractmethod
    def _load_clat_clon(self, grid_uuid: UUID) -> xr.DataArray:
        """Load the clat and clon grid coordinates.

        Parameters
        ----------
        grid_uuid: UUID
            The UUID of the horizontal grid as specified in the GRIB file.

        Raises
        ------
        KeyError
            If the UUID does not match a known model.

        Returns
        -------
        xarray.DataArray
            Coordinates in radians of the ICON grid cell centers for the model.

        """
        pass

    def load(self, grid_uuid: str) -> dict[str, xr.DataArray]:
        """Get ICON native grid coordinates.

        Parameters
        ----------
        grid_uuid : str
            The UUID of the horizontal grid.

        Returns
        -------
        dict[str, xarray.DataArray]
            Geodetic coordinates of the ICON grid cell centers.

        """
        ds = self._load_clat_clon(UUID(grid_uuid))

        rad2deg = 180 / np.pi
        result = ds[["clon", "clat"]].reset_coords() * rad2deg
        return {"lon": result.clon, "lat": result.clat}


@dc.dataclass
class FileGridSource(ICONGridSource):
    """Source that loads ICON grid data from files.

    Parameters
    ----------
    grid_paths: dict[UUID, Path]
        Dictionary mapping from horizontal grid UUID to the path where the data file is.

    """

    grid_paths: dict[UUID, Path]

    def _load_clat_clon(self, grid_uuid: UUID) -> xr.DataArray:
        grid_path = self.grid_paths.get(grid_uuid)
        if grid_path is None:
            raise KeyError("No grid file for UUID %s.", grid_uuid)
        return xr.open_dataset(grid_path)


def get_balfrin_grid_source() -> ICONGridSource:
    """Return a grid source to load grid files when running on balfrin."""
    grid_dir = Path("/scratch/mch/jenkins/icon/pool/data/ICON/mch/grids/")
    grid_paths = {
        UUID("17643da2-5749-59b6-44d2-54a3cd6e2bc0"): grid_dir
        / "icon-1/icon_grid_0001_R19B08_mch.nc",
        UUID("bbbd5a09-8554-9924-3c7a-4aa4c8762920"): grid_dir
        / "icon-2/icon_grid_0002_R19B07_mch.nc",
    }
    return FileGridSource(grid_paths=grid_paths)


class OGDGridSource(ICONGridSource):
    def _load_clat_clon(self, model_name: str) -> xr.DataArray:
        raise NotImplementedError(
            "Loading the ICON grid from OGD is not yet implemented."
        )


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
