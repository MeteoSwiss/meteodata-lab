# Third-party
from earthkit.meteo import thermo  # type: ignore
from numpy.testing import assert_allclose
import earthkit.data as ekd
import yaml
from importlib.resources import files

# First-party
import meteodatalab.operators.thetav as mthetav
from meteodatalab.data_source import FileDataSource
from meteodatalab.grib_decoder import load


def calculate_error(p, t, qv):
    p0 = 1.0e5  # Reference surface pressure
    r_d = 287.05  # Specific gas constant for dry air [J kg-1 K-1]
    r_v = 461.51  # Gas constant for water vapour[J kg-1 K-1]
    cp_d = 1005.0  # Specific heat capacity at constant pressure for dry air [J kg-1 K]
    rdocp = r_d / cp_d
    rvd = r_v / r_d
    rvd_o = rvd - 1.0
    epsilon = 0.621981

    p_np = p.values
    t_np = t.values
    qv_np = qv.values

    c1 = (1.0 - epsilon) / epsilon
    return (p0 / p_np) ** rdocp * t_np * (1.0 + (rvd_o * qv_np / (1.0 - qv_np))) - (
        thermo.potential_temperature(t_np, p_np) * (1.0 + c1 * qv_np)
    )


def test_thetav(data_dir, fieldextra):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    with open(files("meteodatalab.data").joinpath("profile.yaml"), "r") as file:
        profile = yaml.safe_load(file)

    ds = (
        ekd.from_source("file", [str(datafile)])
        .sel(param=["P", "T", "QV"])
        .to_xarray(profile="grib", **profile)
    )

    thetav = mthetav.fthetav(ds["P"], ds["T"], ds["QV"])

    assert thetav.paramId == 500597
    assert thetav.units == "K"
    assert thetav.long_name == "Potential temperature"
    assert thetav.standard_name == "THETA_V"

    fs_ds = fieldextra("THETAV")

    # due to the difference in constants from earthkit-meteo and fieldextra
    err = calculate_error(ds["P"], ds["T"], ds["QV"])

    assert_allclose(fs_ds["THETA_V"] - err, thetav, rtol=1e-6)
