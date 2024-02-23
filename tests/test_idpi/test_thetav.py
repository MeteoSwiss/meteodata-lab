# Third-party
from numpy.testing import assert_allclose

# First-party
import idpi.operators.thetav as mthetav
from idpi.grib_decoder import GribReader


def test_thetav(data_dir, fieldextra):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    reader = GribReader.from_files([datafile])

    ds = reader.load_fieldnames(["P", "T", "QV"])
    thetav = mthetav.fthetav(ds["P"], ds["T"], ds["QV"])

    fs_ds = fieldextra("THETAV")

    assert_allclose(fs_ds["THETA_V"], thetav, rtol=1e-6)
