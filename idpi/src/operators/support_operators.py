"""algorithms to support operations on a field."""

import numpy as np
import xarray as xr


def init_field(parent: xr.DataArray, fill_value, dtype=None, vcoord=None) -> xr.DataArray:
    # Initialize a new field with some meta-information
    attrs = parent.attrs.copy()
    shape = list(len(parent[d]) for d in parent.dims)
    dims = list(parent.dims)
    coords = dict(parent.coords)
    
    if vcoord is None:
        return xr.full_like(parent, fill_value, dtype)  
      
    else:
        # attrs
        attrs = parent.attrs.copy()
        attrs["GRIB_typeOfLevel"] = vcoord["typeOfLevel"]
        if attrs["GRIB_NV"] is not None:
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
       
