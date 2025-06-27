# Third-party
import pytest
import xarray as xr
from numpy.testing import assert_allclose

# First-party
import meteodatalab.operators.pot_vortic as pv
from meteodatalab.data_cache import DataCache
from meteodatalab.data_source import FDBDataSource
from meteodatalab.grib_decoder import load
from meteodatalab.metadata import set_origin_xy
from meteodatalab.operators.rho import compute_rho_tot
from meteodatalab import physical_constants as pc
from meteodatalab import metadata


def compute_theta(p, t):
    p0 = 1.0e5
    return xr.DataArray(
        data=(p0 / p) ** pc.rdocp * t,
        attrs=metadata.override(p.metadata, shortName="PT"),
    )


@pytest.fixture
def data(work_dir, request_template, setup_fdb):
    source = FDBDataSource(request_template=request_template)
    fields = {
        "inputi": [(p, "ml") for p in ("U", "V", "W", "P", "T", "QV", "QC", "QI")],
        "inputc": [("HHL", "ml"), ("HSURF", "sfc"), ("FIS", "sfc")],
    }
    files = {
        "inputi": "lfff<ddhh>0000",
        "inputc": "lfff00000000c",
    }
    cache = DataCache(cache_dir=work_dir, fields=fields, files=files)
    cache.populate(source)
    yield source, cache
    cache.clear()


def test_pv(data, fieldextra):
    source, cache = data
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

    conf_files = cache.conf_files | {"output": "<hh>_outfile.nc"}
    fs_ds = fieldextra("POT_VORTIC", conf_files=conf_files)

    assert_allclose(
        fs_ds["POT_VORTIC"],
        observed,
        rtol=1e-4,
        atol=1e-8,
    )
