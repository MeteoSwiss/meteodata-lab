# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from meteodatalab.data_source import FileDataSource
from meteodatalab.grib_decoder import load
from meteodatalab.operators.hzerocl import fhzerocl
from importlib.resources import files


@pytest.mark.parametrize("extrapolate", [True, False])
def test_hzerocl(data_dir, fieldextra, extrapolate):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    source = FileDataSource(datafiles=[str(datafile), str(cdatafile)])
    ds = load(source, {"param": ["T", "HHL"]})

    import earthkit.data as ekd

    import yaml

    profile = files("meteodatalab.data").joinpath("profile.yaml")

    with open(profile, "r") as file:
        profile = yaml.safe_load(file)

    ds_t = (
        ekd.from_source("file", [str(datafile)])
        .sel(param="T")
        .to_xarray(profile="grib", **profile)
    )

    ds_hhl = (
        ekd.from_source("file", [str(cdatafile)])
        .sel(param="HHL")
        .to_xarray(profile="grib", **profile)
    )

    hzerocl = fhzerocl(ds_t["T"], ds_hhl["HHL"], extrapolate)

    assert hzerocl.paramId == 500127
    assert hzerocl.units == "m"
    assert hzerocl.standard_name == "hzerocl"

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
