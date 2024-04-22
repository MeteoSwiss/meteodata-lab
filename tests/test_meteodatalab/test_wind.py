# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from idpi.data_cache import DataCache
from idpi.data_source import DataSource
from idpi.grib_decoder import GribReader
from idpi.metadata import set_origin_xy
from idpi.operators import wind


@pytest.fixture
def data(work_dir, request_template, setup_fdb):
    source = DataSource(request_template=request_template)
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
    reader = GribReader.from_files(cache.populated_files)
    ds = reader.load_fieldnames(["U_10M", "V_10M"])
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
