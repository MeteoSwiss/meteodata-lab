"""algorithm for computing omega_slope."""

# Third-party
import numpy as np
import xarray as xr

# Local
from .. import metadata
from .. import physical_constants as pc


# similar to the subtract.accumulate but permute the order of the operans of the diff
# TODO implement as a ufunc
def cumdiff(A, axis):
    r = np.empty(np.shape(A))
    t = 0  # op = the ufunc being applied to A's  elements
    for i in range(np.shape(A)[axis]):
        t = np.take(A, i, axis) - t

        slices = []
        for dim in range(A.ndim):
            if dim == axis:
                slices.append(slice(i, i + 1))
            else:
                slices.append(slice(None))

        r[tuple(slices)] = np.expand_dims(t, axis=axis)
    return r


def omega_slope(
    ps: xr.DataArray, etadot: xr.DataArray, ak: xr.DataArray, bk: xr.DataArray
):
    """Compute the omega slope.

    Converts ECMWF etadot (deta/dt) to etadot * dp/deta, required by FLEXPART.

    Parameters
    ----------
    ps : xarray.DataArray
        Pressure (S) (not reduced) in Pa.
    etadot : xarray.DataArray
        Eta-coordinate vertical velocity (deta/dt) in s**-1.
    ak : xarray.DataArray
        Hybrid level A coefficient.
    bk : xarray.DataArray
        Hybrid level B coefficient.


    Returns
    -------
    xarray.DataArray
        Vertical velocity (pressure) in Pa s**-1.

    Notes
    -----
    Fieldextra returns the parameter as ETADOT.

    """
    dak_dz = ak.diff(dim="z")
    dbk_dz = bk.diff(dim="z")

    res = (
        2.0
        * etadot
        * ps
        * (dak_dz / ps + dbk_dz)
        / (dak_dz / pc.surface_pressure_ref + dbk_dz)
    ).reduce(cumdiff, dim="z")

    return xr.DataArray(
        data=res,
        attrs=metadata.override(
            # Eta-coordinate vertical velocity
            etadot.metadata,
            discipline=0,
            parameterCategory=2,
            parameterNumber=32,
        ),
    )
