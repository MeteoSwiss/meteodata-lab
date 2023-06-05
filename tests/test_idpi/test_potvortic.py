# Third-party
import numpy as np
from numpy.testing import assert_allclose

# First-party
import idpi.operators.pot_vortic as pv
from idpi import grib_decoder
from idpi.operators.rho import f_rho_tot
from idpi.operators.theta import ftheta
from idpi.operators.total_diff import TotalDiff


def test_pv(data_dir, fieldextra, grib_defs):
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    ds = {}
    grib_decoder.load_data(
        ds, ["U", "V", "W", "P", "T", "QV", "QC", "QI"], datafile, chunk_size=None
    )
    grib_decoder.load_data(ds, ["HHL", "HSURF"], cdatafile, chunk_size=None)

    theta = ftheta(ds["P"], ds["T"])
    rho_tot = f_rho_tot(ds["T"], ds["P"], ds["QV"], ds["QC"], ds["QI"])

    dlon = ds["HHL"].attrs["GRIB_iDirectionIncrementInDegrees"]
    dlat = ds["HHL"].attrs["GRIB_jDirectionIncrementInDegrees"]
    deg2rad = np.pi / 180

    total_diff = TotalDiff(dlon * deg2rad, dlat * deg2rad, ds["HHL"])

    observed = pv.fpotvortic(ds["U"], ds["V"], ds["W"], theta, rho_tot, total_diff)

    fs_ds = fieldextra("POT_VORTIC")
    expected = fs_ds.rename(
        {"x_1": "x", "y_1": "y", "z_1": "generalVerticalLayer"}
    ).squeeze(drop=True)

    assert_allclose(
        observed,
        expected,
        rtol=1e-4,
        atol=1e-8,
    )
