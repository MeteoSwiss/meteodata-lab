"""ICON native grid helper functions."""

# Standard library
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
    def _load_clat_clon(self, model_name: str) -> xr.DataArray:
        """Load the clat and clon grid coordinates.

        Parameters
        ----------
        model_name: str
            The name of the model that the grid applies to. Expected to be one of
            "icon-ch1-eps" or "icon-ch2-eps".

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

        Raises
        ------
        KeyError
            If the UUID does not match a known model.

        Returns
        -------
        dict[str, xarray.DataArray]
            Geodetic coordinates of the ICON grid cell centers.

        """
        model_name = GRID_UUID_TO_MODEL.get(UUID(grid_uuid))

        if model_name is None:
            raise KeyError("Unknown UUID: ", grid_uuid)
        ds = self._load_clat_clon(model_name)

        rad2deg = 180 / np.pi
        result = ds[["clon", "clat"]].reset_coords() * rad2deg
        return {"lon": result.clon, "lat": result.clat}


class FileGridSource(ICONGridSource):
    def __init__(self, grid_paths: dict[str, Path]):
        self._grid_paths = grid_paths

    def _load_grid_from_file(self, grid_path: Path) -> xr.DataArray:
        return xr.open_dataset(grid_path)

    def _load_clat_clon(self, model_name: str) -> xr.DataArray:
        grid_path = self._grid_paths.get(model_name)
        if grid_path is None:
            raise KeyError("No grid file for model %s.", model_name)
        return self._load_grid_from_file(grid_path)


class CSCSGridSource(FileGridSource):
    """Special case of FileGridSource with file locations in CSCS."""

    GRID_DIR = Path("/scratch/mch/jenkins/icon/pool/data/ICON/mch/grids/")
    GRID_MAP = {
        "icon-ch1-eps": GRID_DIR / "icon-1/icon_grid_0001_R19B08_mch.nc",
        "icon-ch2-eps": GRID_DIR / "icon-2/icon_grid_0002_R19B07_mch.nc",
    }

    def __init__(self):
        super().__init__(self.GRID_MAP)


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
