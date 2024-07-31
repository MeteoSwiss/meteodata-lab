# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from meteodatalab.grib_decoder import GribReader
from meteodatalab.operators.relhum import relhum

expected_water = {
    "centre": "lssw",
    "paramId": 500037,
    "shortName": "RELHUM",
    "units": "%",
    "name": "Relative Humidity",
}

expected_ice = {
    "centre": "lssw",
    "paramId": 503195,
    "shortName": "RH_ICE",
    "units": "%",
    "name": "relative humidity over ice",
}
expected_mixed = {
    "centre": "lssw",
    "paramId": 503078,
    "shortName": "RH_MIX_EC",
    "units": "%",
    "name": "Relative humidity over mixed phase",
}


@pytest.mark.parametrize(
    "phase,field,expected",
    [
        ("water", "RELHUM", expected_water),
        ("ice", "RH_ICE", expected_ice),
        ("water+ice", "RH_MIX_EC", expected_mixed),
    ],
)
def test_relhum(data_dir, fieldextra, phase, field, expected):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    reader = GribReader.from_files([cdatafile, datafile])
    ds = reader.load_fieldnames(["P", "T", "QV"])

    relhum_arr = relhum(ds["QV"], ds["T"], ds["P"], clipping=True, phase=phase)
    if phase == "water+ice":
        print("relhum_arr")
        print(relhum_arr)
        print(relhum_arr.parameter)
    assert relhum_arr.parameter == expected

    fs_ds = fieldextra("RELHUM", field=field)
    assert_allclose(fs_ds[field], relhum_arr, rtol=5e-3, atol=5e-2)
