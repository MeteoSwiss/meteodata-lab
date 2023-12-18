# Third-party
from numpy.testing import assert_allclose

# First-party
import idpi.operators.brn as mbrn
from idpi.grib_decoder import GribReader


def test_brn(data_dir, fieldextra):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    reader = GribReader.from_files([cdatafile, datafile])
    ds = reader.load_fieldnames(["P", "T", "QV", "U", "V", "HHL", "HSURF"])

    brn = mbrn.fbrn(
        ds["P"], ds["T"], ds["QV"], ds["U"], ds["V"], ds["HHL"], ds["HSURF"]
    )

    fs_ds = fieldextra("BRN")

    assert_allclose(fs_ds["BRN"], brn, rtol=5e-3, atol=5e-2)
