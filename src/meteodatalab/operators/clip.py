"""Horizontal clipping operator."""

# Standard library
from uuid import UUID, uuid4

# Third-party
import numpy as np
import xarray as xr

# Local
from .. import metadata
from ..icon_grid import load_boundary_idx_from_file


def clip_lateral_boundary_strip(
    field: xr.DataArray,
    strip_idx: int,
    idx: xr.DataArray | None = None,
    new_gridfile: str | None = None,
) -> xr.DataArray:
    """Clip the field to the given lateral boundary strip index.

    This function is used to clip a field lateral boundaries using data from the
    ICON grid descriptor file. Specifically, it uses the indices of the lateral
    boundary strips (`refin_c_ctrl`) to determine which cells to keep. See the ICON
    model tutorial for details [1]_. Note that this function only works with regional
    grids of the ICON model.

    Parameters
    ----------
    field: xr.DataArray
        The field to clip.
    strip_idx: int
        The maximum lateral boundary strip index to keep.
    idx: xr.DataArray, optional
        The lateral boundary strip index to use.
    new_gridfile: str, optional
        The new grid descriptor file to use. This is not implemented yet.

    Raises
    ------
    ValueError
        If the field is not on an unstructured grid.
    NotImplementedError
        If the new grid descriptor file functionality is not implemented yet.

    Returns
    -------
    xr.DataArray
        The clipped field.

    References
    ----------
    [1] ICON model tutorial 2023:
        https://www.cosmo-model.org/content/model/documentation/core/iconTutorial_dwd_2023.pdf

    """
    if not field.metadata.get("gridType") == "unstructured_grid":
        raise ValueError("Field must be on an unstructured grid.")

    if idx is None:
        grid_uuid = UUID(field.metadata.get("uuidOfHGrid"))
        idx = load_boundary_idx_from_file(grid_uuid)

    mask = np.isin(idx.values, np.arange(1, strip_idx + 1))

    # TODO: implement new grid descriptor file functionality
    if new_gridfile is not None:
        raise NotImplementedError(
            "New grid descriptor file functionality is not implemented yet."
        )

    return xr.DataArray(
        field.sel(cell=~mask),
        attrs=metadata.override(
            field.metadata,
            uuidOfHGrid=str(uuid4()).replace("-", ""),
        ),
    )
