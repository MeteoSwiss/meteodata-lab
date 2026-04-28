# Third-party
import numpy as np
from numpy.testing import assert_allclose, assert_equal

# First-party
from meteodatalab.data_source import FileDataSource
from meteodatalab.grib_decoder import load
from meteodatalab.metadata import set_origin_xy
from meteodatalab.operators.destagger import destagger


def test_destagger(data_dir, fieldextra):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    source = FileDataSource(datafiles=[str(datafile), str(cdatafile)])
    ds = load(source, {"param": ["U", "V", "HHL"]})

    set_origin_xy(ds, ref_param="HHL")

    u = destagger(ds["U"], "x")
    v = destagger(ds["V"], "y")
    hfl = destagger(ds["HHL"].isel(lead_time=0), "z")

    fs_ds = fieldextra("destagger")

    assert_allclose(fs_ds["U"], u, rtol=1e-12, atol=1e-9)
    assert_allclose(fs_ds["V"], v, rtol=1e-12, atol=1e-9)
    assert_allclose(fs_ds["HFL"], hfl, rtol=1e-12, atol=1e-9)

    hhl = ds["HHL"]
    assert_allclose(u.lon, hhl.lon)
    assert_allclose(u.lat, hhl.lat)
    assert_allclose(v.lon, hhl.lon)
    assert_allclose(v.lat, hhl.lat)

    assert u.geography == hhl.geography
    assert v.geography == hhl.geography
    assert hfl.geography == hhl.geography

    assert u.origin_x == 0.0
    assert v.origin_y == 0.0
    assert hfl.origin_z == 0.0

    assert_equal(hfl.z, np.arange(1, 81))
