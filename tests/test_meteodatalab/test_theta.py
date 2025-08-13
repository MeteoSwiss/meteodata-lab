# Third-party
from numpy.testing import assert_allclose
import earthkit.data as ekd
import yaml
from importlib.resources import files

# First-party
from meteodatalab.operators.theta import compute_theta


def calculate_error(p, t):
    p0 = 1.0e5  # Reference surface pressure
    r_d = 287.05  # Specific gas constant for dry air [J kg-1 K-1]
    cp_d = 1005.0  # Specific heat capacity at constant pressure for dry air [J kg-1 K]
    rdocp = r_d / cp_d
    kappa = 0.285691

    p_np = p.values
    t_np = t.values
    return ((p0 / p_np) ** rdocp - (p0 / p_np) ** kappa) * t_np


def test_theta(data_dir, fieldextra):

    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"

    with open(files("meteodatalab.data").joinpath("profile.yaml"), "r") as file:
        profile = yaml.safe_load(file)

    ds = (
        ekd.from_source("file", [str(datafile)])
        .sel(param=["T", "P"])
        .to_xarray(profile="grib", **profile)
    )

    theta = compute_theta(ds["P"], ds["T"])

    assert theta.paramId == 502693
    assert theta.units == "K"
    assert theta.long_name == "Potential temperature"
    assert theta.standard_name == "PT"

    fs_ds = fieldextra("THETA")

    # due to the difference in constants from earthkit-meteo and fieldextra
    err = calculate_error(ds["P"], ds["T"])

    assert_allclose(fs_ds["THETA"] - err, theta, rtol=1e-6)
