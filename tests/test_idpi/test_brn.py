# Third-party
from numpy.testing import assert_allclose

# First-party
import idpi.operators.brn as mbrn
from idpi.grib_decoder import GribReader


def test_brn(data_dir, fieldextra):
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    reader = GribReader([cdatafile, datafile])
    ds = reader.load_fieldnames(["P", "T", "QV", "U", "V", "HHL", "HSURF"])

    brn = mbrn.fbrn(
        ds["P"], ds["T"], ds["QV"], ds["U"], ds["V"], ds["HHL"], ds["HSURF"]
    )

    fs_ds = fieldextra("BRN")

    assert_allclose(fs_ds["BRN"], brn, rtol=5e-3, atol=5e-2)
