# Third-party
import numpy as np
import pytest
from numpy.testing import assert_allclose

# First-party
import idpi.operators.pot_vortic as pv
from idpi.data_cache import DataCache
from idpi.data_source import DataSource
from idpi.grib_decoder import GribReader
from idpi.operators.rho import f_rho_tot
from idpi.operators.theta import ftheta
from idpi.operators.total_diff import TotalDiff


@pytest.fixture
def data(work_dir, request_template, setup_fdb):
    source = DataSource(request_template=request_template)
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
    reader = GribReader(source, ref_param=("HHL", "ml"))
    yield reader, cache
    cache.clear()


def test_pv(data, fieldextra):
    reader, cache = data
    ds = reader.load_fieldnames(["U", "V", "W", "P", "T", "QV", "QC", "QI", "HHL"])

    theta = ftheta(ds["P"], ds["T"])
    rho_tot = f_rho_tot(ds["T"], ds["P"], ds["QV"], ds["QC"], ds["QI"])

    geo = ds["HHL"].attrs["geography"]
    dlon = geo["iDirectionIncrementInDegrees"]
    dlat = geo["jDirectionIncrementInDegrees"]
    deg2rad = np.pi / 180

    total_diff = TotalDiff(dlon * deg2rad, dlat * deg2rad, ds["HHL"])

    observed = pv.fpotvortic(ds["U"], ds["V"], ds["W"], theta, rho_tot, total_diff)

    conf_files = cache.conf_files | {"output": "<hh>_outfile.nc"}
    fs_ds = fieldextra("POT_VORTIC", conf_files=conf_files)

    assert_allclose(
        fs_ds["POT_VORTIC"],
        observed,
        rtol=1e-4,
        atol=1e-8,
    )
