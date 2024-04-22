# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from idpi.grib_decoder import GribReader
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
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    # load input data set
    reader = GribReader.from_files([cdatafile, datafile])
    ds = reader.load_fieldnames([field, "HHL"])

    if layer == "half":
        height = ds["HHL"]
    elif layer == "full":
        height = destagger(ds["HHL"], "z")
    else:
        raise RuntimeError(f"Unknown value for layer: {layer}")
    # ATTENTION: attributes are lost in destagger operation

    h_bounds = [
        height.isel(z=k_bottom - 1),
        height.isel(z=k_top - 1),
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
