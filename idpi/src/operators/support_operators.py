"""Algorithms to support operations on a field."""

import typing

import numpy as np
import xarray as xr


def init_field_with_vcoord(
    parent: xr.DataArray,
    vcoord: dict[str, typing.Any],
    fill_value: typing.Any,
    dtype: np.dtype = None,
) -> xr.DataArray:
    """Initialize an xarray.DataArray with new vertical coordinates.

    Properties except for those related to the vertical coordinates, and optionally dtype,
    are inherited from the parent xarray.DataArray.

    Parameters
    ----------
        parent : xarray.DataArray
            parent field
        vcoord : dict[str, typing.Any]
            dictionary specifying new vertical coordinates; defaults to None
            expected keys: "typeOfLevel" (string), "values" (list), "NV" (int), "attrs" (dict)
        fill_value : typing.Any
            value the data array of the new field is initialized with
        dtype : numpy.dtype
            fill value data type; defaults to None (in this case the data type
            is inherited from the parent field)

    Returns
    -------
        init_field_with_vcoord : xarray.DataArray
            new field
    """
    # TODO: test that vertical dim of parent is named "generalVerticalLayer" or take vertical dim to replace as argument
    #       be aware that vcoord contains also xr.DataArray GRIB attributes; one should separate these from coordinate properties
    #       in the interface
    # check vcoord keys
    expected_vcoord_keys = ("typeOfLevel", "NV", "values", "attrs")
    for k in expected_vcoord_keys:
        if k not in vcoord:
            raise KeyError("init_field: missing vcoord key ", k)
    # attrs
    attrs = parent.attrs.copy()
    attrs["GRIB_typeOfLevel"] = vcoord["typeOfLevel"]
    if "GRIB_NV" in attrs:
        attrs["GRIB_NV"] = vcoord["NV"]
    # dims
    shape = list(
        len(parent[d]) if d != "generalVerticalLayer" else len(vcoord["values"])
        for d in parent.dims
    )
    dims = list(
        map(
            lambda x: x.replace("generalVerticalLayer", vcoord["typeOfLevel"]),
            parent.dims,
        )
    )
    # coords
    # ... inherit all except for the vertical coordinates
    coords = {c: v for c, v in parent.coords.items() if c != "generalVerticalLayer"}
    # ... initialize the vertical target coordinates
    coords[vcoord["typeOfLevel"]] = xr.IndexVariable(
        vcoord["typeOfLevel"], vcoord["values"], attrs=vcoord["attrs"]
    )
    # dtype
    if dtype is None:
        dtype = parent.data.dtype

    return xr.DataArray(
        name=parent.name,
        data=np.full(tuple(shape), fill_value, dtype),
        dims=tuple(dims),
        coords=coords,
        attrs=attrs,
    )
