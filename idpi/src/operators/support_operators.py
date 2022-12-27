"""Algorithms to support operations on a field."""

import numpy as np
import xarray as xr


def init_field(parent: xr.DataArray, fill_value, dtype=None, vcoord: dict=None) -> xr.DataArray:
    """ Initializes a new field with some meta meta-information.
    
    Meta-information is inherited from the parent field as long as optional arguments
    are not specified.

    Parameters
    ----------
        parent : xr.DataArray 
            parent field
        fill_value : 
            value the data array of the new field is initialized with
        dtype : 
            fill value data type; defaults to None (in this case the data type
            is inherited from the parent field)
        vcoord (optional) : dict
            dictionary specifying new vertical coordinates; defaults to None
            expected keys: "typeOfLevel" (string), "values" (list), "NV" (int),
                           "attrs" (dict)

    Returns
    -------
        init_field : xr.DataArray
            new field
    """
    
    if vcoord is None:
        return xr.full_like(parent, fill_value, dtype)
      
    else:
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
            map(lambda x: x.replace("generalVerticalLayer", vcoord["typeOfLevel"]), parent.dims)
        )
        # coords
        # ... inherit all except for the vertical coordinates
        coords = {c:v for c,v in parent.coords.items() if c != 'generalVerticalLayer'}
        # ... initialize the vertical target coordinates
        coords[vcoord["typeOfLevel"]] = xr.IndexVariable(vcoord["typeOfLevel"], vcoord["values"], attrs=vcoord["attrs"])
        # dtype
        if dtype is None:
            dtype = parent.data.dtype

        return xr.DataArray(
            name=parent.name, 
            data=np.full(tuple(shape), 
            fill_value, dtype),
            dims=tuple(dims), coords=coords, attrs=attrs
        )
       
