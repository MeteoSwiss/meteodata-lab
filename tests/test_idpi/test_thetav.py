# Third-party
from numpy.testing import assert_allclose

# First-party
import idpi.operators.thetav as mthetav
from idpi import grib_decoder


def test_thetav(data_dir, fieldextra, grib_defs):
    datafile = data_dir / "lfff00000000.ch"

    ds = {}
    grib_decoder.load_data(ds, ["P", "T", "QV"], datafile, chunk_size=None)

    thetav = mthetav.fthetav(ds["P"], ds["T"], ds["QV"])

    fs_ds = fieldextra("THETAV").squeeze()

    assert_allclose(fs_ds["THETA_V"], thetav, rtol=1e-6)
