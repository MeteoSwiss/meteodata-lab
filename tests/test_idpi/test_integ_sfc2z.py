# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from idpi.grib_decoder import GribReader
from idpi.operators.destagger import destagger
from idpi.operators.vertical_reduction import integrate_k


@pytest.mark.parametrize("field,k_max", [("T", 80), ("W", 81)])
@pytest.mark.parametrize(
    "operator,fx_op,atol,rtol",
    [("integral", "integ", 1e-4, 1e-6), ("normed_integral", "norm_integ", 1e-5, 1e-6)],
)
def test_integ_sfc2z(field, k_max, operator, fx_op, atol, rtol, data_dir, fieldextra):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    # modes
    mode = "z2z"

    # h_bounds (count starting with 1), h_bottom is given by HSURF
    k_top = 61

    # load input data set
    reader = GribReader.from_files([cdatafile, datafile])
    ds = reader.load_fieldnames([field, "HHL", "HSURF"])

    hhl = ds["HHL"]
    hfl = destagger(hhl, "z")
    hsurf = ds["HSURF"]
    h_bounds = [hsurf, hfl.isel(z=k_top - 1)]

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

    # compare numerical results
    assert_allclose(
        fx_ds[field].isel(z_1=0),
        f_bar,
        rtol=rtol,
        atol=atol,
        equal_nan=True,
    )
