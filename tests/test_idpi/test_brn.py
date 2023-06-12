# Third-party
from numpy.testing import assert_allclose

# First-party
import idpi.operators.brn as mbrn
from idpi import grib_decoder


def test_brn(data_dir, fieldextra, grib_defs):
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    ds = {}
    grib_decoder.load_data(ds, ["P", "T", "QV", "U", "V"], datafile, chunk_size=None)
    grib_decoder.load_data(ds, ["HHL", "HSURF"], cdatafile, chunk_size=None)

    brn = mbrn.fbrn(
        ds["P"], ds["T"], ds["QV"], ds["U"], ds["V"], ds["HHL"], ds["HSURF"]
    )

    fs_ds = fieldextra("BRN")
    brn_ref = (
        fs_ds["BRN"]
        .rename({"x_1": "x", "y_1": "y", "z_1": "generalVerticalLayer"})
        .squeeze()
    )

    assert_allclose(brn_ref, brn, rtol=5e-3, atol=5e-2, equal_nan=True)
