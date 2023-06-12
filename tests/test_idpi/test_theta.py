# Third-party
from numpy.testing import assert_allclose

# First-party
import idpi.operators.theta as mtheta
from idpi import grib_decoder


def test_theta(data_dir, fieldextra, grib_defs):
    datafile = data_dir / "lfff00000000.ch"

    ds = {}
    grib_decoder.load_data(ds, ["P", "T"], datafile, chunk_size=None)

    theta = mtheta.ftheta(ds["P"], ds["T"])

    fs_ds = fieldextra("THETA").squeeze()

    assert_allclose(fs_ds["THETA"], theta, rtol=1e-6)
