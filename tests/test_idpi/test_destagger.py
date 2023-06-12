# Third-party
from numpy.testing import assert_allclose

# First-party
from idpi import grib_decoder
from idpi.operators.destagger import destagger


def test_destagger(data_dir, fieldextra, grib_defs):
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    ds = {}
    grib_decoder.load_data(ds, ["U", "V"], datafile, chunk_size=None)
    grib_decoder.load_data(ds, ["HHL"], cdatafile, chunk_size=None)

    u = destagger(ds["U"], "x")
    v = destagger(ds["V"], "y")
    hfl = destagger(ds["HHL"], "generalVertical")

    fs_ds = fieldextra("destagger")
    fields = ["U", "V", "HFL"]
    name_map = {"x_1": "x", "y_1": "y", "z_1": "generalVerticalLayer"}
    ref = {k: fs_ds[k].rename(name_map).squeeze() for k in fields}

    assert_allclose(ref["U"], u, rtol=1e-12, atol=1e-9, equal_nan=True)
    assert_allclose(ref["V"], v, rtol=1e-12, atol=1e-9, equal_nan=True)
    assert_allclose(ref["HFL"], hfl, rtol=1e-12, atol=1e-9, equal_nan=True)
