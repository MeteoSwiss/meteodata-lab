# Third-party
from numpy.testing import assert_allclose

# First-party
from meteodatalab.grib_decoder import GribReader
from meteodatalab.operators.theta import compute_theta


def test_theta(data_dir, fieldextra):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    reader = GribReader.from_files([datafile])

    ds = reader.load_fieldnames(["P", "T"])

    theta = compute_theta(ds["P"], ds["T"])

    assert theta.parameter == {
        "centre": "lssw",
        "paramId": 502693,
        "shortName": "PT",
        "units": "K",
        "name": "Potential temperature",
    }

    fs_ds = fieldextra("THETA")

    assert_allclose(fs_ds["THETA"], theta, rtol=1e-6)
