# Third-party
from numpy.testing import assert_allclose

# First-party
import idpi.operators.thetav as mthetav
from idpi.grib_decoder import GribReader


def test_thetav(data_dir, fieldextra):
    datafile = data_dir / "lfff00000000.ch"

    reader = GribReader([datafile], ref_param="P")

    ds = reader.load_fieldnames(["P", "T", "QV"])
    thetav = mthetav.fthetav(ds["P"], ds["T"], ds["QV"])

    fs_ds = fieldextra("THETAV")

    assert_allclose(fs_ds["THETA_V"], thetav, rtol=1e-6)
