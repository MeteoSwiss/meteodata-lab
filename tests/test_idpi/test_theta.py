# Third-party
from numpy.testing import assert_allclose

# First-party
import idpi.operators.theta as mtheta
from idpi.grib_decoder import GribReader


def test_theta(data_dir, fieldextra):
    datafile = data_dir / "lfff00000000.ch"

    reader = GribReader.from_files([datafile], ref_param="P")

    ds = reader.load_fieldnames(["P", "T"])

    theta = mtheta.ftheta(ds["P"], ds["T"])

    fs_ds = fieldextra("THETA")

    assert_allclose(fs_ds["THETA"], theta, rtol=1e-6)
