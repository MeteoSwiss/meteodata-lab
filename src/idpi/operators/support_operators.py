"""Algorithms to support operations on a field."""


# Standard library
import dataclasses as dc
from typing import Any, Literal, Optional, Sequence

# Third-party
import numpy as np
import xarray as xr


@dc.dataclass
class TargetCoordinatesAttrs:
    """Attributes to the target coordinates."""

    standard_name: str
    long_name: str
    units: str
    positive: Literal["up", "down"]


@dc.dataclass
class TargetCoordinates:
    """Target Coordinates."""

    type_of_level: str
    values: Sequence[float]
    attrs: TargetCoordinatesAttrs

    @property
    def size(self):
        return len(self.values)


def init_field_with_vcoord(
    parent: xr.DataArray,
    vcoord: TargetCoordinates,
    fill_value: Any,
    dtype: Optional[np.dtype] = None,
) -> xr.DataArray:
    """Initialize an xarray.DataArray with new vertical coordinates.

    Properties except for those related to the vertical coordinates,
    and optionally dtype, are inherited from the parent xarray.DataArray.

    Parameters
    ----------
    parent : xr.DataArray
        parent field
    vcoord: TargetCoordinates
        target vertical coordinates for the output field
    fill_value : Any
        value the data array of the new field is initialized with
    dtype : np.dtype, optional
        fill value data type; defaults to None (in this case
        the data type is inherited from the parent field)

    Returns
    -------
    xr.DataArray
        new field located at the parent field horizontal coordinates, the target
        coordinates in the vertical and filled with the given value

    """
    # TODO: test that vertical dim of parent is named "generalVerticalLayer"
    # or take vertical dim to replace as argument
    #       be aware that vcoord contains also xr.DataArray GRIB attributes;
    #  one should separate these from coordinate properties
    #       in the interface
    # attrs
    attrs = parent.attrs.copy()
    attrs["vcoord_type"] = vcoord.type_of_level

    # dims
    def replace_vertical(items):
        for dim, size in items:
            if dim == "z":
                yield vcoord.type_of_level, vcoord.size
            else:
                yield dim, size

    # ... make sure to maintain the ordering of the dims
    sizes = {dim: size for dim, size in replace_vertical(parent.sizes.items())}
    # coords
    # ... inherit all except for the vertical coordinates
    coords = {c: v for c, v in parent.coords.items() if c != "z"}
    # ... initialize the vertical target coordinates
    coords[vcoord.type_of_level] = xr.IndexVariable(
        vcoord.type_of_level, vcoord.values, attrs=dc.asdict(vcoord.attrs)
    )
    # dtype
    if dtype is None:
        dtype = parent.data.dtype

    return xr.DataArray(
        name=parent.name,
        data=np.full(tuple(sizes.values()), fill_value, dtype),
        dims=tuple(sizes.keys()),
        coords=coords,
        attrs=attrs,
    )


def get_grid_coords(n: int, x0: float, dx: float, dim: str) -> xr.DataArray:
    """Compute coordinates for an equally spaced grid.

    Values are rounded to the 6th decimal because the data representation
    in the GRIB specification calls for integers values in microdegrees.
    It is assumed that data input will in the GRIB format and thus subject
    to this property.

    Parameters
    ----------
    n : int
        Number of grid points
    x0 : float
        Coordinates of the origin in the given dimension
    dx : float
        Spacing of the grid along the given dimension
    dim : str
        Dimension along which the grid is defined

    Returns
    -------
    xr.DataArray
        A 1-D field containing the coordinates of the grid along the given dimension

    """
    values = np.arange(n) * dx + x0
    return xr.DataArray(np.round(values, 6), dims=dim)
