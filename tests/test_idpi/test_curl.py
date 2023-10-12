# Third-party
import numpy as np
from xarray.testing import assert_allclose

# First-party
from idpi.grib_decoder import GribReader
from idpi.operators import curl
from idpi.operators.support_operators import get_grid_coords
from idpi.operators.total_diff import TotalDiff


def test_curl(data_dir):
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    reader = GribReader([cdatafile, datafile])
    ds = reader.load_fields(["U", "V", "W", "HHL"])

    geo = ds["HHL"].attrs["geography"]
    dlon = geo["iDirectionIncrementInDegrees"]
    dlat = geo["jDirectionIncrementInDegrees"]
    nj = geo["Nj"]
    lat_min = geo["latitudeOfFirstGridPointInDegrees"]

    deg2rad = np.pi / 180
    rlat = get_grid_coords(nj, lat_min, dlat, "y") * deg2rad
    total_diff = TotalDiff(dlon * deg2rad, dlat * deg2rad, ds["HHL"])

    a1, a2, a3 = curl.curl(ds["U"], ds["V"], ds["W"], rlat, total_diff)
    b1, b2, b3 = curl.curl_alt(ds["U"], ds["V"], ds["W"], rlat, total_diff)

    s = dict(x=slice(1, -1), y=slice(1, -1), z=slice(1, -1))
    assert_allclose(a1[s], b1[s])
    assert_allclose(a2[s], b2[s])
    assert_allclose(a3[s], b3[s])
