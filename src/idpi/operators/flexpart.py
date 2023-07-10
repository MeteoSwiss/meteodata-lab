"""Flexpart operators."""

# Third-party
import numpy as np

# First-party
from idpi.operators.omega_slope import omega_slope
from idpi.operators.time_operators import time_rate


def fflexpart(ds):
    ds_out = {}
    for field in (
        "U",
        "V",
        "T",
        "QV",
        "PS",
        "U_10M",
        "V_10M",
        "T_2M",
        "TD_2M",
        "CLCT",
        "W_SNOW",
    ):
        ds_out[field] = ds[field].isel(time=slice(1, None))

    ds_out["TOT_CON"] = time_rate(ds["TOT_CON"], np.timedelta64(1, "h"))
    ds_out["TOT_GSP"] = time_rate(ds["TOT_GSP"], np.timedelta64(1, "h"))

    ds_out["ASOB_S"] = time_rate(ds["ASOB_S"], np.timedelta64(1, "s"))
    ds_out["ASHFL_S"] = time_rate(ds["ASHFL_S"], np.timedelta64(1, "s"))
    ds_out["EWSS"] = time_rate(ds["EWSS"], np.timedelta64(1, "s"))

    ds_out["OMEGA"] = omega_slope(ds["PS"], ds["ETADOT"], ds["ak"], ds["bk"]).isel(
        z=slice(39, 137), time=slice(1, None)
    )

    return ds_out
