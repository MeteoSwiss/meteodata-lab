# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from idpi import grib_decoder
from idpi.operators.destagger import destagger
from idpi.operators.vertical_reduction import integrate_k


@pytest.mark.parametrize("field,k_max", [("T", 80), ("W", 81)])
@pytest.mark.parametrize(
    "operator,fx_op",
    [("integral", "integ"), ("normed_integral", "norm_integ")],
)
def test_integ_z2z(field, k_max, operator, fx_op, data_dir, fieldextra, grib_defs):
    # modes
    mode = "z2z"

    # k indices defining h_bounds (count starting with 1)
    k_bottom = 61
    k_top = 60

    # input data
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    # load input data set
    ds = {}
    grib_decoder.load_data(ds, [field], datafile, chunk_size=None)
    grib_decoder.load_data(ds, ["HHL"], cdatafile, chunk_size=None)
    hhl = ds["HHL"]
    hfl = destagger(hhl, "generalVertical")
    # ATTENTION: attributes are lost in destagger operation
    h_bounds = [
        hfl.isel(generalVerticalLayer=k_bottom - 1),
        hfl.isel(generalVerticalLayer=k_top - 1),
    ]

    # call integral operator
    f_bar = integrate_k(ds[field], operator, mode, hhl, h_bounds)

    fx_ds = fieldextra(
        "integ_z2z_for_h_k",
        operator=fx_op,
        field=field,
        mode=mode,
        kmax=k_max,
        kbottom=k_bottom,
        ktop=k_top,
    )

    f_bar_ref = (
        fx_ds[field].rename({"x_1": "x", "y_1": "y", "epsd_1": "number"}).squeeze()
    )

    # compare numerical results
    assert_allclose(
        f_bar_ref,
        f_bar,
        rtol=1e-6,
        atol=1e-5,
        equal_nan=True,
    )
