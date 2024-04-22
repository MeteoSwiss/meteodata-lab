"""Flexpart operators."""

# Third-party
import numpy as np

# First-party
from idpi.operators.omega_slope import omega_slope
from idpi.operators.time_operators import time_rate


def fflexpart(ds):
    ds_out = {}
    for field in (
        "u",
        "v",
        "t",
        "q",
        "sp",
        "10u",
        "10v",
        "2t",
        "2d",
        "tcc",
        "sd",
    ):
        ds_out[field] = ds[field].isel(time=slice(1, None))

    ds_out["cp"] = time_rate(ds["cp"], np.timedelta64(1, "h"))
    ds_out["lsp"] = time_rate(ds["lsp"], np.timedelta64(1, "h"))

    ds_out["ssr"] = time_rate(ds["ssr"], np.timedelta64(1, "s"))
    ds_out["sshf"] = time_rate(ds["sshf"], np.timedelta64(1, "s"))
    ds_out["ewss"] = time_rate(ds["ewss"], np.timedelta64(1, "s"))
    ds_out["nsss"] = time_rate(ds["nsss"], np.timedelta64(1, "s"))

    ds_out["omega"] = omega_slope(ds["sp"], ds["etadot"], ds["ak"], ds["bk"]).isel(
        z=slice(39, 137), time=slice(1, None)
    )

    return ds_out
