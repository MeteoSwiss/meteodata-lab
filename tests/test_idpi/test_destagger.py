# Third-party
from numpy.testing import assert_allclose

# First-party
from idpi.grib_decoder import GribReader
from idpi.operators.destagger import destagger


def test_destagger(data_dir, fieldextra):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    reader = GribReader.from_files([cdatafile, datafile])
    ds = reader.load_fieldnames(
        ["U", "V", "HHL"],
    )

    u = destagger(ds["U"], "x")
    v = destagger(ds["V"], "y")
    hfl = destagger(ds["HHL"].isel(time=0), "z")

    fs_ds = fieldextra("destagger")

    assert_allclose(fs_ds["U"], u, rtol=1e-12, atol=1e-9)
    assert_allclose(fs_ds["V"], v, rtol=1e-12, atol=1e-9)
    assert_allclose(fs_ds["HFL"], hfl, rtol=1e-12, atol=1e-9)

    assert u.origin["x"] == 0.0
    assert v.origin["y"] == 0.0
    assert hfl.origin["z"] == 0.0
