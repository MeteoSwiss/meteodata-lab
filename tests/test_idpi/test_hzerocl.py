# Third-party
from numpy.testing import assert_allclose

# First-party
from idpi import grib_decoder
from idpi.operators.hzerocl import fhzerocl


def test_hzerocl(data_dir, fieldextra, grib_defs):
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    ds = {}
    grib_decoder.load_data(ds, ["T"], datafile, chunk_size=None)
    grib_decoder.load_data(ds, ["HHL"], cdatafile, chunk_size=None)

    hzerocl = fhzerocl(ds["T"], ds["HHL"])

    fs_ds = fieldextra("hzerocl")
    hzerocl_ref = fs_ds["HZEROCL"].rename({"x_1": "x", "y_1": "y"}).squeeze()

    assert_allclose(
        hzerocl_ref,
        hzerocl,
        rtol=1e-6,
        atol=1e-5,
        equal_nan=True,
    )
