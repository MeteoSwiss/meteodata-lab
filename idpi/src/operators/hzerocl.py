"""algorithm for computation of height of zero degree isotherm (without extrapolation below model orography)."""
from operators.destagger import destagger
import xarray as xr
import numpy as np


def fhzerocl(t, hhl):
    t0 = 273.15
    hfl = destagger(hhl, "generalVerticalLayer")
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

    tkp1 = t.copy()
    tkp1[{"generalVerticalLayer": slice(0, -1)}] = t[
        {"generalVerticalLayer": slice(1, None)}
    ].assign_coords(
        {
            "generalVerticalLayer": t[
                {"generalVerticalLayer": slice(0, -1)}
            ].generalVerticalLayer
        }
    )

    # Initiailize hzerocl with missing values
    hzerocl = xr.full_like(hfl[{"generalVerticalLayer": 0}], np.nan)

    # 3d field with values of height for those levels where temperature is > 0 and it was
    # < 0 on the level below. Otherwise values are NaN.
    height2 = hfl.where((t >= t0) & (tkm1 < t0), drop=True)
    if height2.size > 0:
        # The previous condition can be satisfied on multiple levels.
        # Take the k indices of the maximum height value where the condition is satisfied
        maxind = height2.fillna(-1).argmax(dim=["generalVerticalLayer"])
        # compute the 2D fields with height values where T is > 0 and < 0 on level below
        height2 = height2[{"generalVerticalLayer": maxind["generalVerticalLayer"]}]
        # compute the 2D fields with height values where T is < 0 and > 0 on level above
        height1 = hfl.where((tkp1 >= t0) & (t < t0), drop=True)[
            {"generalVerticalLayer": maxind["generalVerticalLayer"]}
        ]
        # the height leve where T == 0 must be between [height1, height2]
        t1 = t.where((t >= t0) & (tkm1 < t0), drop=True)[
            {"generalVerticalLayer": maxind["generalVerticalLayer"]}
        ]

        t2 = t.where((tkp1 >= t0) & (t < t0), drop=True)[
            {"generalVerticalLayer": maxind["generalVerticalLayer"]}
        ]
        w1 = (t1 - t0) / (t1 - t2)
        w2 = (t0 - t2) / (t1 - t2)

        hzerocl = w1 * height1 + w2 * height2

    return hzerocl
