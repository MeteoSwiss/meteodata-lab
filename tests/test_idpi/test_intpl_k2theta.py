# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from idpi.grib_decoder import GribReader
from idpi.operators.destagger import destagger
from idpi.operators.theta import compute_theta
from idpi.operators.vertical_interpolation import interpolate_k2theta


# @pytest.mark.parametrize("mode", ["high_fold", "low_fold", "undef_fold"])
@pytest.mark.parametrize("mode", ["high_fold", "low_fold"])
def test_intpl_k2theta(mode, data_dir, fieldextra):
    # define target coordinates
    tc_values = [280.0, 290.0, 310.0, 315.0, 320.0, 325.0, 330.0, 335.0]
    fx_voper_lev = ",".join(str(int(v)) for v in tc_values)
    tc_units = "K"

    # input data
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    # load input data set
    reader = GribReader.from_files([cdatafile, datafile])

    ds = reader.load_fieldnames(["P", "T", "HHL"])

    theta = compute_theta(ds["P"], ds["T"])
    hfl = destagger(ds["HHL"].squeeze(drop=True), "z")

    # call interpolation operator
    t = interpolate_k2theta(ds["T"], mode, theta, tc_values, tc_units, hfl)

    fx_ds = fieldextra(
        "intpl_k2theta",
        mode=mode,
        voper_lev=fx_voper_lev,
        voper_lev_units=tc_units,
    )

    # compare numerical results
    assert_allclose(fx_ds["T"], t, rtol=1e-4, atol=1e-4, equal_nan=True)
