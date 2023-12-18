# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from idpi.grib_decoder import GribReader
from idpi.operators.hzerocl import fhzerocl


@pytest.mark.parametrize("extrapolate", [True, False])
def test_hzerocl(data_dir, fieldextra, extrapolate):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    reader = GribReader.from_files([cdatafile, datafile])
    ds = reader.load_fieldnames(
        ["T", "HHL"],
    )

    hzerocl = fhzerocl(ds["T"], ds["HHL"], extrapolate)

    fs_ds = fieldextra(
        "hzerocl",
        h0cl_extrapolate=".true." if extrapolate else ".false.",
    )

    assert_allclose(
        fs_ds["HZEROCL"],
        hzerocl,
        rtol=5e-6,
        atol=1e-5,
        equal_nan=True,
    )
