# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from idpi import grib_decoder
from idpi.operators.destagger import destagger
from idpi.operators.vertical_reduction import minmax_k


@pytest.mark.parametrize("operator,fx_op", [("maximum", "max"), ("minimum", "min")])
@pytest.mark.parametrize("field,layer", [("T", "full"), ("W", "half")])
def test_minmax_z2z(operator, fx_op, field, layer, data_dir, fieldextra):
    # modes
    mode = "z2z"

    # k indices defining h_bounds (count starting with 1)
    k_bottom = 61
    k_top = 60

    # input data
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    # load input data set
    ds = grib_decoder.load_cosmo_data(
        [field, "HHL"],
        [datafile, cdatafile],
    )

    if layer == "half":
        height = ds["HHL"]
        z = "generalVertical"
    elif layer == "full":
        height = destagger(ds["HHL"], "generalVertical")
        z = "generalVerticalLayer"
    else:
        raise RuntimeError(f"Unknown value for layer: {layer}")
    # ATTENTION: attributes are lost in destagger operation

    h_bounds = [
        height.isel({z: k_bottom - 1}),
        height.isel({z: k_top - 1}),
    ]

    # call reduction operator
    f_minmax = minmax_k(ds[field], operator, mode, height, h_bounds)

    fx_ds = fieldextra(
        f"minmax_{mode}_for_h_k_{layer}",
        minmax=fx_op,
        field=field,
        mode=mode,
        kbottom=k_bottom,
        ktop=k_top,
    )

    # compare numerical results
    assert_allclose(
        fx_ds[field].isel(z_1=0),
        f_minmax,
        rtol=1e-6,
        atol=1e-5,
        equal_nan=True,
    )
