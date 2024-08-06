# Third-party
import numpy as np
from xarray.testing import assert_allclose

# First-party
from meteodatalab.data_source import FileDataSource
from meteodatalab.grib_decoder import load
from meteodatalab.metadata import set_origin_xy
from meteodatalab.operators import curl
from meteodatalab.operators.gis import get_grid
from meteodatalab.operators.total_diff import TotalDiff


def test_curl(data_dir):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    source = FileDataSource(datafiles=[cdatafile, datafile])
    ds = load(source, {"param": ["U", "V", "W", "HHL"]})
    set_origin_xy(ds, ref_param="HHL")

    deg2rad = np.pi / 180
    rlat = get_grid(ds["HHL"].attrs["geography"]).rlat * deg2rad
    total_diff = TotalDiff.from_hhl(ds["HHL"])

    a1, a2, a3 = curl.curl(ds["U"], ds["V"], ds["W"], rlat, total_diff)
    b1, b2, b3 = curl.curl_alt(ds["U"], ds["V"], ds["W"], rlat, total_diff)

    s = dict(x=slice(1, -1), y=slice(1, -1), z=slice(1, -1))
    assert_allclose(a1[s], b1[s])
    assert_allclose(a2[s], b2[s])
    assert_allclose(a3[s], b3[s])
