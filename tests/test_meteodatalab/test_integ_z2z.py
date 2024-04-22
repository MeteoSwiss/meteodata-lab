# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from idpi.grib_decoder import GribReader
from idpi.operators.destagger import destagger
from idpi.operators.vertical_reduction import integrate_k


@pytest.mark.parametrize("field,k_max", [("T", 80), ("W", 81)])
@pytest.mark.parametrize(
    "operator,fx_op",
    [("integral", "integ"), ("normed_integral", "norm_integ")],
)
def test_integ_z2z(field, k_max, operator, fx_op, data_dir, fieldextra):
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
    hhl = ds["HHL"]
    hfl = destagger(hhl, "z")
    # ATTENTION: attributes are lost in destagger operation
    h_bounds = [
        hfl.isel(z=k_bottom - 1),
        hfl.isel(z=k_top - 1),
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
        f_bar.squeeze(),  # fx has no eps nor step dims
        rtol=1e-6,
        atol=1e-5,
        equal_nan=True,
    )
