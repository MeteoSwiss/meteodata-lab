"""Horizontal clipping operator."""

# Standard library
from uuid import UUID, uuid5

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
        The lateral boundary strip index to use. This is the `refin_c_ctrl` variable
        from the ICON grid descriptor file. If not provided, it will be loaded from
        the grid descriptor file using the `uuidOfHGrid` attribute of the field.
        Providing the `idx` is useful if you want to use this operator multiple times
        and want to avoid reading the grid descriptor file multiple times.
    new_gridfile: str, optional
        If provided, the new grid descriptor file will be saved to this path. In order
        to read back the clipped data, the new grid descriptor file must be provided to
        the `geo_coords` callback of the `grib_decoder.load` function. It is only needed
        once.

    Raises
    ------
    ValueError
        If the field is not on an unstructured grid.
    ValueError
        If the provided grid descriptor file does not match the field's UUID.

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

    original_grid_uuid = UUID(field.metadata.get("uuidOfHGrid"))

    if idx is None:
        idx = load_boundary_idx_from_file(original_grid_uuid)
        if idx.attrs["uuidOfHGrid"].replace("-", "") != original_grid_uuid.hex:
            raise ValueError(
                "The provided grid descriptor file does not match the field's UUID."
            )

    mask = np.isin(idx.values, np.arange(1, strip_idx + 1))

    # Create a deterministic UUID from the original UUID and the strip_idx
    new_uuid = uuid5(original_grid_uuid, str(strip_idx))

    if new_gridfile is not None:
        idx = idx.reset_coords()[["clon", "clat"]].sel(cell=~mask)  # type: ignore
        idx.attrs = {"uuidOfHGrid": str(new_uuid)}
        idx.to_netcdf(new_gridfile)

    field = field.sel(cell=~mask)
    return xr.DataArray(
        field,
        attrs=metadata.override(
            field.metadata,
            uuidOfHGrid=new_uuid.hex,
            numberOfDataPoints=field.size,
        ),
    )
