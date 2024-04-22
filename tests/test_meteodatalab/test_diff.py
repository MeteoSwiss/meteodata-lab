# Third-party
import numpy as np
from numpy.testing import assert_allclose

# First-party
from idpi.grib_decoder import GribReader
from idpi.operators import diff
from idpi.operators.theta import compute_theta


def test_masspoint_field(data_dir):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    reader = GribReader.from_files([datafile])

    ds = reader.load_fieldnames(["P", "T"])

    theta = compute_theta(ds["P"], ds["T"])

    padding = [(0, 0)] * 2 + [(1, 1)] * 3
    tp = np.pad(theta, padding, mode="edge")
    tp[..., :, :, 0] = tp[..., :, :, -1] = np.nan
    tp[..., :, 0, :] = tp[..., :, -1, :] = np.nan
    dt_dx = 0.5 * (tp[..., 1:-1, 1:-1, 2:] - tp[..., 1:-1, 1:-1, :-2])
    dt_dy = 0.5 * (tp[..., 1:-1, 2:, 1:-1] - tp[..., 1:-1, :-2, 1:-1])
    dt_dz = 0.5 * (tp[..., 2:, 1:-1, 1:-1] - tp[..., :-2, 1:-1, 1:-1])
    dt_dz[..., 0, :, :] *= 2
    dt_dz[..., -1, :, :] *= 2

    assert_allclose(diff.dx(theta), dt_dx)
    assert_allclose(diff.dy(theta), dt_dy)
    assert_allclose(diff.dz(theta), dt_dz)


def test_staggered_field(data_dir):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    reader = GribReader.from_files([datafile])

    ds = reader.load_fieldnames(["W"])

    w = ds["W"]
    wn = w.to_numpy()
    dw_dz = wn[..., 1:, :, :] - wn[..., :-1, :, :]

    assert_allclose(diff.dz_staggered(w), dw_dz)
