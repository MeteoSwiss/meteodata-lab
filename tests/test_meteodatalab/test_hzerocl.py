# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from meteodatalab.data_source import FileDataSource
from meteodatalab.grib_decoder import load
from meteodatalab.operators.hzerocl import fhzerocl


@pytest.mark.parametrize("extrapolate", [True, False])
def test_hzerocl(data_dir, fieldextra, extrapolate):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    source = FileDataSource(datafiles=[str(datafile), str(cdatafile)])
    ds = load(source, {"param": ["T", "HHL"]})

    import earthkit.data as ekd

    import yaml

    with open("/scratch/mch/cosuna/meteodata-lab/extract_profile.yaml", "r") as file:
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

    print("AAA", ds_t["T"])

    print("BBB", ds_hhl["HHL"])
    hzerocl = fhzerocl(ds_t["T"], ds_hhl["HHL"], extrapolate)

    assert hzerocl.parameter == {
        "centre": "lssw",
        "paramId": 500127,
        "shortName": "HZEROCL",
        "units": "m",
        "name": "Height of 0 degree Celsius isotherm above msl",
    }


#    fs_ds = fieldextra(
#        "hzerocl",
#        h0cl_extrapolate=".true." if extrapolate else ".false.",
#    )

#    assert_allclose(
#        fs_ds["HZEROCL"],
#        hzerocl,
#        rtol=5e-6,
#        atol=1e-5,
#        equal_nan=True,
#    )
