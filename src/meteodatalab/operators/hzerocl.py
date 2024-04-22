"""Algorithm for computation of height of zero degree isotherm."""

# Standard library
from typing import cast

# Third-party
import numpy as np
import xarray as xr

# First-party
from idpi.operators.destagger import destagger


def fhzerocl(
    t: xr.DataArray, hhl: xr.DataArray, extrapolate: bool = False
) -> xr.DataArray:
    """Height of the zero deg C isotherm in m amsl.

    The algorithm searches from the top of the atmosphere downwards.
    When extrapolation is enabled, the search may extend past the lowest
    layers of the model by means of a linear model. The resulting height
    may be below the surface of the earth.

    Parameters
    ----------
    t : xr.DataArray
        Air temperature in K.
    hhl : xr.DataArray
        Heights of the interfaces between vertical layers in m amsl.
    extrapolate : bool, optional
        Allow the extrapolation of the search below the lowest model layer.
        Defaults to False.

    Returns
    -------
    xr.DataArray
        Height of the zero deg C isotherm in m amsl.

    """
    # Physical constants
    t0 = 273.15

    # Heights of layer mid surfaces (where t is defined)
    hfl = destagger(hhl, "z")

    tkm1 = t.shift(z=1)

    # 3d field with values of height for those levels where temperature
    # is > 0 and it was < 0 on the level below. Otherwise values are NaN.
    height0 = hfl.where((t >= t0) & (tkm1 < t0))

    # The previous condition can be satisfied on multiple levels.
    # Take the k indices of the maximum height value where the condition is satisfied
    maxind = cast(xr.DataArray, height0.fillna(-1).argmax(dim="z"))

    if extrapolate:
        # The full column is below freezing
        below_ground = (t < t0).all("z")
        # Temperature is increasing with decreasing altitude
        positive_dt = t[{"z": -1}] - t[{"z": -2}] > 1e-10
        # Allow t0 to be outside of the [height1, height2] range
        cond = np.logical_and(below_ground, positive_dt)
        maxind = maxind.where(~cond, -1)

    # Compute the 2D fields with height values where T is > 0 and < 0 on level below
    height2 = hfl[{"z": maxind}]
    # Compute the 2D fields with height values where T is < 0 and > 0 on level above
    height1 = hfl[{"z": maxind - 1}]
    # The height level where T == t0 must be between [height1, height2]
    t2 = t[{"z": maxind}]
    t1 = tkm1[{"z": maxind}]

    hzerocl = height1 + (height2 - height1) * (t0 - t1) / (t2 - t1)

    return hzerocl.where(hzerocl > 0)
