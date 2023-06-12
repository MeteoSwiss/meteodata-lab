# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from idpi import grib_decoder
from idpi.operators.destagger import destagger
from idpi.operators.vertical_reduction import integrate_k


@pytest.mark.parametrize("field,k_max", [("T", 80), ("W", 81)])
@pytest.mark.parametrize(
    "operator,fx_op,atol,rtol",
    [("integral", "integ", 1e-4, 1e-6), ("normed_integral", "norm_integ", 1e-5, 1e-6)],
)
def test_integ_sfc2z(
    field, k_max, operator, fx_op, atol, rtol, data_dir, fieldextra, grib_defs
):
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    # modes
    mode = "z2z"

    # h_bounds (count starting with 1), h_bottom is given by HSURF
    k_top = 61

    # load input data set
    ds = {}
    grib_decoder.load_data(ds, [field], datafile, chunk_size=None)
    grib_decoder.load_data(ds, ["HHL", "HSURF"], cdatafile, chunk_size=None)

    hhl = ds["HHL"]
    hfl = destagger(hhl, "generalVertical")
    hsurf = ds["HSURF"]
    h_bounds = [hsurf, hfl[k_top - 1]]

    # call integral operator
    f_bar = integrate_k(ds[field], operator, mode, hhl, h_bounds)

    fx_ds = fieldextra(
        "integ_sfc2z_for_h_k",
        operator=fx_op,
        field=field,
        mode=mode,
        ktop=k_top,
        kmax=k_max,
    )
    f_bar_ref = (
        fx_ds[field].rename({"x_1": "x", "y_1": "y", "epsd_1": "number"}).squeeze()
    )

    # compare numerical results
    assert_allclose(
        f_bar_ref,
        f_bar,
        rtol=rtol,
        atol=atol,
        equal_nan=True,
    )
