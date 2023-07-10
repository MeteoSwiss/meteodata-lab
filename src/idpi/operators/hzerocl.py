"""Algorithm for computation of height of zero degree isotherm.

This is done without extrapolation below model orography.
"""
# Third-party
import xarray as xr

# First-party
from idpi.operators.destagger import destagger


def fhzerocl(t: xr.DataArray, hhl: xr.DataArray) -> xr.DataArray:
    """Height of the zero deg C isotherm in m amsl.

    The algorithm searches from the top of the atmosphere downwards.
    No extrapolation below the earth's surface is done.

    Args:
        t (xarray.DataArray): air temperature in K
        hhl (xarray.DataArray): heights of the interfaces between
            vertical layers in m amsl

    Returns:
        xarray.DataArray: height of the zero deg C isotherm in m amsl

    """
    # Physical constants
    t0 = 273.15

    # Heights of layer mid surfaces (where t is defined)
    hfl = destagger(hhl, "z")

    tkm1 = t.shift(z=1)

    # 3d field with values of height for those levels where temperature
    # is > 0 and it was < 0 on the level below. Otherwise values are NaN.
    height2 = hfl.where((t >= t0) & (tkm1 < t0))

    # The previous condition can be satisfied on multiple levels.
    # Take the k indices of the maximum height value where the condition is satisfied
    maxind: xr.DataArray = height2.fillna(-1).argmax(dim="z")  # type: ignore
    # Compute the 2D fields with height values where T is > 0 and < 0 on level below
    height2 = height2[{"z": maxind}]
    # Compute the 2D fields with height values where T is < 0 and > 0 on level above
    height1 = hfl[{"z": maxind - 1}]
    # The height level where T == t0 must be between [height1, height2]
    t2 = t[{"z": maxind}]
    t1 = tkm1[{"z": maxind}]

    hzerocl = height1 + (height2 - height1) * (t0 - t1) / (t2 - t1)

    return hzerocl
