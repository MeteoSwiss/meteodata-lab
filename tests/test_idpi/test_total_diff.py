# Third-party
import numpy as np
from numpy.testing import assert_allclose

# First-party
from idpi import grib_decoder
from idpi.operators import diff
from idpi.operators.theta import ftheta
from idpi.operators.total_diff import TotalDiff


def test_total_diff(data_dir, grib_defs):
    cdatafile = data_dir / "lfff00000000c.ch"

    ds = {}
    grib_decoder.load_data(ds, ["HHL"], cdatafile, chunk_size=None)

    deg2rad = np.pi / 180

    hhl = ds["HHL"].values
    dlon = ds["HHL"].attrs["GRIB_iDirectionIncrementInDegrees"] * deg2rad
    dlat = ds["HHL"].attrs["GRIB_jDirectionIncrementInDegrees"] * deg2rad

    inv_dlon = 1 / dlon
    inv_dlat = 1 / dlat
    hhlp = np.pad(hhl, ((0, 0), (1, 1), (1, 1)), constant_values=np.nan)

    sqrtg_r_s = 1 / (hhl[:-1] - hhl[1:])
    dzeta_dlam = (
        0.25
        * inv_dlon
        * sqrtg_r_s
        * (
            (hhlp[:-1, 1:-1, 2:] - hhlp[:-1, 1:-1, :-2])
            + (hhlp[1:, 1:-1, 2:] - hhlp[1:, 1:-1, :-2])
        )
    )
    dzeta_dphi = (
        0.25
        * inv_dlat
        * sqrtg_r_s
        * (
            (hhlp[:-1, 2:, 1:-1] - hhlp[:-1, :-2, 1:-1])
            + (hhlp[1:, 2:, 1:-1] - hhlp[1:, :-2, 1:-1])
        )
    )

    total_diff = TotalDiff(dlon, dlat, ds["HHL"])

    assert_allclose(total_diff.sqrtg_r_s.values, sqrtg_r_s)
    assert_allclose(total_diff.dzeta_dlam.values, dzeta_dlam, rtol=1e-6)
    assert_allclose(total_diff.dzeta_dphi.values, dzeta_dphi, rtol=1e-6)

    datafile = data_dir / "lfff00000000.ch"

    grib_decoder.load_data(ds, ["P", "T"], datafile, chunk_size=None)
    theta = ftheta(ds["P"], ds["T"])

    tp = np.pad(theta, 1, mode="edge")
    dt_dx = 0.5 * (tp[1:-1, 1:-1, 2:] - tp[1:-1, 1:-1, :-2])
    dt_dy = 0.5 * (tp[1:-1, 2:, 1:-1] - tp[1:-1, :-2, 1:-1])
    dt_dz = 0.5 * (tp[2:, 1:-1, 1:-1] - tp[:-2, 1:-1, 1:-1])
    dt_dz[0] *= 2
    dt_dz[-1] *= 2

    dt_dlam = dt_dx / dlon + dzeta_dlam * dt_dz
    dt_dphi = dt_dy / dlat + dzeta_dphi * dt_dz
    dt_dzeta = dt_dz * sqrtg_r_s

    assert_allclose(
        dt_dlam, total_diff.d_dlam(diff.dx(theta), diff.dz(theta)), rtol=1e-5, atol=1e-2
    )
    assert_allclose(
        dt_dphi, total_diff.d_dphi(diff.dy(theta), diff.dz(theta)), rtol=1e-5, atol=1e-2
    )
    assert_allclose(dt_dzeta, total_diff.d_dzeta(diff.dz(theta)), rtol=1e-5, atol=1e-3)
