# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from meteodatalab.data_cache import DataCache
from meteodatalab.data_source import FDBDataSource, FileDataSource
from meteodatalab.grib_decoder import load
from meteodatalab.metadata import set_origin_xy
from meteodatalab.operators import wind


@pytest.fixture
def data(work_dir, request_template, setup_fdb):
    source = FDBDataSource(request_template=request_template)
    fields = {
        "inputi": [(p, "sfc") for p in ("U_10M", "V_10M")],
    }
    files = {
        "inputi": "lfff<ddhh>0000",
    }
    cache = DataCache(cache_dir=work_dir, fields=fields, files=files)
    cache.populate(source)
    yield cache
    cache.clear()


def test_wind(data, fieldextra):
    cache = data
    source = FileDataSource(datafiles=[str(f) for f in cache.populated_files])
    ds = load(source, {"param": ["U_10M", "V_10M"]})
    set_origin_xy(ds, ref_param="U_10M")

    u_10m = ds["U_10M"].isel(z=0)
    v_10m = ds["V_10M"].isel(z=0)

    ff_10m = wind.speed(u_10m, v_10m)
    dd_10m = wind.direction(u_10m, v_10m)

    conf_files = cache.conf_files | {"output": "<hh>_outfile.nc"}
    fx_ds = fieldextra("wind", conf_files=conf_files)

    assert_allclose(ff_10m, fx_ds["FF_10M"], rtol=1e-6)
    assert_allclose(dd_10m, fx_ds["DD_10M"], atol=1e-4)

    assert ff_10m.parameter == {
        "centre": "lssw",
        "name": "Wind speed (SP_10M)",
        "paramId": 500025,
        "shortName": "SP_10M",
        "units": "m s-1",
    }

    assert dd_10m.parameter == {
        "centre": "lssw",
        "name": "Wind Direction (DD_10M)",
        "paramId": 500023,
        "shortName": "DD_10M",
        "units": "degree true",
    }


@pytest.mark.data("iconremap")
@pytest.mark.parametrize("model_name", ["icon-ch1-eps", "icon-ch2-eps"])
def test_wind_icon(data_dir, fieldextra, model_name, geo_coords):
    datafiles = [str(data_dir / f"{model_name.upper()}_lfff00000000_000")]
    source = FileDataSource(datafiles=datafiles)
    ds = load(source, {"param": ["U_10M", "V_10M"]}, geo_coords=geo_coords)

    u_10m = ds["U_10M"].isel(z=0)
    v_10m = ds["V_10M"].isel(z=0)

    ff_10m = wind.speed(u_10m, v_10m)
    dd_10m = wind.direction(u_10m, v_10m)

    conf_files = {
        "inputi": data_dir / f"{model_name.upper()}_lfff<DDHH>0000_000",
        "output": "<HH>_outfile.nc",
    }
    root = "/oprusers/osm/opr.emme/data/ICON_INPUT"
    icon_grid_description = {
        "icon-ch1-eps": f"{root}/ICON-CH1-EPS/icon_grid_0001_R19B08_mch.nc",
        "icon-ch2-eps": f"{root}/ICON-CH2-EPS/icon_grid_0002_R19B07_mch.nc",
    }
    fx_ds = fieldextra(
        "wind_icon",
        model_name=model_name,
        icon_grid_description=icon_grid_description[model_name],
        conf_files=conf_files,
    )

    assert_allclose(ff_10m, fx_ds["FF_10M"], rtol=1e-6)
    assert_allclose(dd_10m, fx_ds["DD_10M"], atol=1e-4)

    assert ff_10m.parameter == {
        "centre": "lssw",
        "name": "Wind speed (SP_10M)",
        "paramId": 500025,
        "shortName": "SP_10M",
        "units": "m s-1",
    }

    assert dd_10m.parameter == {
        "centre": "lssw",
        "name": "Wind Direction (DD_10M)",
        "paramId": 500023,
        "shortName": "DD_10M",
        "units": "degree true",
    }
