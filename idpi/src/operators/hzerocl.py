"""algorithm for computation of height of zero degree isotherm (without extrapolation below model orography)."""
import numpy as np
from operators.destagger import destagger


def fhzerocl(t, hhl):
    """Height of the zero deg C isotherm in m amsl.

    The algorithm searches from the top of the atmosphere downwards.
    No extrapolation below the earth's surface is done.

    Parameters
    ----------
        t : xarray.DataArray
            air temperature in K
        hhl : xarray.DataArray
            heights of the interfaces between vertical layers in m amsl

    Returns
    -------
        hzerocl: xarray.DataArray
            height of the zero deg C isotherm in m amsl

    """
    # Physical constants
    t0 = 273.15

    # Heights of layer mid surfaces (where t is defined)
    hfl = destagger(hhl, "generalVertical")

    tkm1 = t.copy()
    tkm1[{"generalVerticalLayer": slice(1, None)}] = t[
        {"generalVerticalLayer": slice(0, -1)}
    ].assign_coords(
        {
            "generalVerticalLayer": t[
                {"generalVerticalLayer": slice(1, None)}
            ].generalVerticalLayer
        }
    )
    tkm1[{"generalVerticalLayer": 0}] = np.nan

    # 3d field with values of height for those levels where temperature is > 0 and it was
    # < 0 on the level below. Otherwise values are NaN.
    height2 = hfl.where((t >= t0) & (tkm1 < t0))

    # The previous condition can be satisfied on multiple levels.
    # Take the k indices of the maximum height value where the condition is satisfied
    maxind = height2.fillna(-1).argmax(dim=["generalVerticalLayer"])
    # Compute the 2D fields with height values where T is > 0 and < 0 on level below
    height2 = height2[{"generalVerticalLayer": maxind["generalVerticalLayer"]}]
    # Compute the 2D fields with height values where T is < 0 and > 0 on level above
    height1 = hfl[{"generalVerticalLayer": maxind["generalVerticalLayer"] - 1}]
    # The height level where T == t0 must be between [height1, height2]
    t2 = t[{"generalVerticalLayer": maxind["generalVerticalLayer"]}]
    t1 = tkm1[{"generalVerticalLayer": maxind["generalVerticalLayer"]}]

    hzerocl = height1 + (height2 - height1) * (t0 - t1) / (t2 - t1)

    return hzerocl
