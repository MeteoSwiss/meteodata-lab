# Standard library
import time
from contextlib import contextmanager

# Third-party
import numpy as np
from xarray.testing import assert_allclose

# First-party
from idpi import grib_decoder
from idpi.operators import curl
from idpi.operators.total_diff import TotalDiff


@contextmanager
def print_time(name):
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"{name} took {elapsed:.3f} s")


def test_curl(data_dir, grib_defs):
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    ds = {}
    grib_decoder.load_data(ds, ["U", "V", "W"], datafile, chunk_size=None)
    grib_decoder.load_data(ds, ["HHL", "HSURF"], cdatafile, chunk_size=None)

    dlon = ds["HHL"].attrs["GRIB_iDirectionIncrementInDegrees"]
    dlat = ds["HHL"].attrs["GRIB_jDirectionIncrementInDegrees"]
    deg2rad = np.pi / 180

    total_diff = TotalDiff(dlon * deg2rad, dlat * deg2rad, ds["HHL"])
    lat = ds["HHL"]["latitude"] * deg2rad

    with print_time("curl"):
        a1, a2, a3 = curl.curl(ds["U"], ds["V"], ds["W"], lat, total_diff)
    with print_time("curl_alt"):
        b1, b2, b3 = curl.curl_alt(ds["U"], ds["V"], ds["W"], lat, total_diff)

    s = dict(x=slice(1, -1), y=slice(1, -1), generalVerticalLayer=slice(1, -1))
    assert_allclose(a1[s], b1[s])
    assert_allclose(a2[s], b2[s])
    assert_allclose(a3[s], b3[s])
