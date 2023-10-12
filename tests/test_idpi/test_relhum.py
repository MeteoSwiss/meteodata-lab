# Third-party
from numpy.testing import assert_allclose

# First-party
from idpi.grib_decoder import GribReader
from idpi.operators.relhum import relhum


def test_relhum(data_dir, fieldextra):
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    reader = GribReader([cdatafile, datafile], ref_param="P")
    ds = reader.load_fields(["P", "T", "QV"])

    relhum_arr = relhum(ds["QV"], ds["T"], ds["P"], clipping=True, phase="water")

    fs_ds = fieldextra("RELHUM")

    assert_allclose(fs_ds["RELHUM"], relhum_arr, rtol=5e-3, atol=5e-2)
