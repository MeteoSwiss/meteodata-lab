# Third-party
from numpy.testing import assert_allclose

# First-party
from idpi import grib_decoder
from idpi.operators.destagger import destagger


def test_destagger(data_dir, fieldextra):
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    ds = grib_decoder.load_cosmo_data(
        ["U", "V", "HHL"],
        [datafile, cdatafile],
    )

    u = destagger(ds["U"], "x")
    v = destagger(ds["V"], "y")
    hfl = destagger(ds["HHL"], "generalVertical")

    fs_ds = fieldextra("destagger")

    assert_allclose(fs_ds["U"], u, rtol=1e-12, atol=1e-9)
    assert_allclose(fs_ds["V"], v, rtol=1e-12, atol=1e-9)
    assert_allclose(fs_ds["HFL"], hfl.isel(step=0), rtol=1e-12, atol=1e-9)
