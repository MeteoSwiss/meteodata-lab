# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from idpi import grib_decoder
from idpi.operators.destagger import destagger
from idpi.operators.theta import ftheta
from idpi.operators.vertical_interpolation import interpolate_k2theta


# @pytest.mark.parametrize("mode", ["high_fold", "low_fold", "undef_fold"])
@pytest.mark.parametrize("mode", ["high_fold", "low_fold"])
def test_intpl_k2theta(mode, data_dir, fieldextra, grib_defs):
    # define target coordinates
    tc_values = [280.0, 290.0, 310.0, 315.0, 320.0, 325.0, 330.0, 335.0]
    fx_voper_lev = ",".join(str(int(v)) for v in tc_values)
    tc_units = "K"

    # input data
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    # load input data set
    ds = {}
    grib_decoder.load_data(ds, ["T", "P"], datafile, chunk_size=None)
    grib_decoder.load_data(ds, ["HHL"], cdatafile, chunk_size=None)

    theta = ftheta(ds["P"], ds["T"])
    hfl = destagger(ds["HHL"], "generalVertical")

    # call interpolation operator
    t = interpolate_k2theta(ds["T"], mode, theta, tc_values, tc_units, hfl)

    fx_ds = fieldextra(
        "intpl_k2theta",
        mode=mode,
        voper_lev=fx_voper_lev,
        voper_lev_units=tc_units,
    )
    t_ref = (
        fx_ds["T"]
        .rename({"x_1": "x", "y_1": "y", "z_1": "theta", "epsd_1": "number"})
        .squeeze()
    )

    # compare numerical results
    assert_allclose(t_ref, t, rtol=1e-4, atol=1e-4, equal_nan=True)
