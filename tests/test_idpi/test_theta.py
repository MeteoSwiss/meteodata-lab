# Third-party
from numpy.testing import assert_allclose

# First-party
from idpi.grib_decoder import GribReader
from idpi.operators.theta import compute_theta


def test_theta(data_dir, fieldextra):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    reader = GribReader.from_files([datafile])

    ds = reader.load_fieldnames(["P", "T"])

    theta = compute_theta(ds["P"], ds["T"])

    fs_ds = fieldextra("THETA")

    assert_allclose(fs_ds["THETA"], theta, rtol=1e-6)
