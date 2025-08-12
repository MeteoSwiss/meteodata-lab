# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from meteodatalab.data_source import FileDataSource
from meteodatalab.grib_decoder import load
from meteodatalab.operators.vertical_interpolation import interpolate_k2p


@pytest.mark.parametrize(
    "mode,fx_mode,atol,rtol",
    [
        ("nearest_sfc", "nearest", 0, 0),
        ("linear_in_p", "lin_p", 1e-5, 1e-7),
        ("linear_in_lnp", "lin_lnp", 1e-5, 1e-6),
    ],
)
def test_intpl_k2p(mode, fx_mode, atol, rtol, data_dir, fieldextra):
    # define target coordinates
    tc_values = [40.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1100.0]
    fx_voper_lev = ",".join(str(int(v)) for v in tc_values)
    tc_units = "hPa"

    # input data
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    source = FileDataSource(datafiles=[datafile, cdatafile])
    ds = load(source, {"param": ["P", "T"]})

    # call interpolation operator
    t = interpolate_k2p(ds["T"], mode, ds["P"], tc_values, tc_units)

    fx_ds = fieldextra("intpl_k2p", mode=fx_mode, voper_lev=fx_voper_lev)

    # compare numerical results
    assert_allclose(fx_ds["T"], t, rtol=rtol, atol=atol, equal_nan=True)
