# Third-party
from numpy.testing import assert_allclose

# First-party
import meteodatalab.operators.pot_vortic as pv
from meteodatalab.data_source import FileDataSource
from meteodatalab.grib_decoder import load
from meteodatalab.metadata import set_origin_xy
from meteodatalab.operators.internal.theta import compute_theta
from meteodatalab.operators.rho import compute_rho_tot


def test_pv(data_dir, fieldextra):

    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    source = FileDataSource(datafiles=[cdatafile, datafile])
    ds = load(source, {"param": ["U", "V", "W", "P", "T", "QV", "QC", "QI", "HHL"]})
    set_origin_xy(ds, ref_param="HHL")

    theta = compute_theta(ds["P"], ds["T"])
    rho_tot = compute_rho_tot(ds["T"], ds["P"], ds["QV"], ds["QC"], ds["QI"])

    assert rho_tot.parameter == {
        "centre": "lssw",
        "name": "Density",
        "paramId": 500545,
        "shortName": "DEN",
        "units": "kg m-3",
    }

    observed = pv.compute_pot_vortic(
        ds["U"], ds["V"], ds["W"], theta, rho_tot, ds["HHL"]
    )

    fs_ds = fieldextra("POT_VORTIC")

    assert_allclose(
        fs_ds["POT_VORTIC"],
        observed,
        rtol=1e-4,
        atol=1e-8,
    )
