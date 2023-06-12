# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from idpi import grib_decoder
from idpi.operators.destagger import destagger
from idpi.operators.vertical_interpolation import interpolate_k2p


@pytest.mark.parametrize(
    "mode,fx_mode,rtol",
    [
        ("nearest_sfc", "nearest", 0),
        ("linear_in_p", "lin_p", 1e-6),
        ("linear_in_lnp", "lin_lnp", 1e-5),
    ],
)
def test_intpl_hk2p(mode, fx_mode, rtol, data_dir, fieldextra, grib_defs):
    # define target coordinates
    tc_values = [300.0, 700.0, 900.0, 1100.0]
    fx_voper_lev = ",".join(str(int(v)) for v in tc_values)
    tc_units = "hPa"

    # input data
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    # load input data set
    ds = {}
    grib_decoder.load_data(ds, ["P"], datafile, chunk_size=None)
    grib_decoder.load_data(ds, ["HHL"], cdatafile, chunk_size=None)
    hhl = ds["HHL"]
    hfl = destagger(hhl, "generalVertical")
    # ATTENTION: attributes are lost in destagger operation

    # call interpolation operator
    hpl = interpolate_k2p(hfl, mode, ds["P"], tc_values, tc_units)

    fx_ds = fieldextra(
        "intpl_hk2p",
        mode=fx_mode,
        voper_lev=fx_voper_lev,
    )

    h_ref = (
        fx_ds["HEIGHT"]
        .rename({"x_1": "x", "y_1": "y", "z_1": "isobaricInPa", "epsd_1": "number"})
        .squeeze()
    )

    # compare numerical results
    assert_allclose(h_ref, hpl, rtol=rtol, atol=0, equal_nan=True)
