# Third-party
import numpy as np
import pytest
from numpy.testing import assert_allclose

# First-party
import idpi.operators.lateral_operators as lat_ops
from idpi.grib_decoder import GribReader
from idpi.operators.hzerocl import fhzerocl


def test_fill_undef(data_dir, fieldextra):
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    reader = GribReader.from_files([cdatafile, datafile])
    ds = reader.load_fieldnames(["T", "HHL"])

    hzerocl = fhzerocl(ds["T"], ds["HHL"])

    observed = lat_ops.fill_undef(hzerocl, 10, 0.3)

    fx_ds = fieldextra("lat_ops_fill_undef")
    expected = fx_ds["HZEROCL"]

    assert_allclose(observed, expected, rtol=2e-6)


def test_disk_avg(data_dir, fieldextra):
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    reader = GribReader.from_files([cdatafile, datafile])

    ds = reader.load_fieldnames(
        ["T", "HHL"],
    )

    hzerocl = fhzerocl(ds["T"], ds["HHL"])

    observed = lat_ops.disk_avg(hzerocl, 10)

    fx_ds = fieldextra("lat_ops_disk_avg")
    expected = fx_ds["HZEROCL"]

    assert_allclose(observed, expected, rtol=2e-6)


@pytest.fixture
def disk_mask():
    return [
        [0, 0, 1, 0, 0],
        [0, 1, 1, 1, 0],
        [1, 1, 1, 1, 1],
        [0, 1, 1, 1, 0],
        [0, 0, 1, 0, 0],
    ]


@pytest.fixture
def exp_weights():
    r0 = 1.0
    r1 = 1 / np.exp(1)
    r2 = 1 / np.exp(2)
    s2 = 1 / np.exp(np.sqrt(2))
    s5 = 1 / np.exp(np.sqrt(5))
    s8 = 1 / np.exp(np.sqrt(8))
    return [
        [s8, s5, r2, s5, s8],
        [s5, s2, r1, s2, s5],
        [r2, r1, r0, r1, r2],
        [s5, s2, r1, s2, s5],
        [s8, s5, r2, s5, s8],
    ]


def test_compute_weights_const_square():
    observed = lat_ops.compute_weights(5, "const", "square")
    expected = np.ones((5, 5))

    assert_allclose(observed, expected)


def test_compute_weights_const_disk(disk_mask):
    observed = lat_ops.compute_weights(5, "const", "disk")
    expected = np.array(disk_mask)

    assert_allclose(observed, expected)


def test_compute_weights_exp_square(exp_weights):
    observed = lat_ops.compute_weights(5, "exp", "square")
    expected = np.array(exp_weights)

    assert_allclose(observed, expected)


def test_compute_weights_exp_disk(disk_mask, exp_weights):
    observed = lat_ops.compute_weights(5, "exp", "disk")
    expected = np.array(disk_mask) * np.array(exp_weights)

    assert_allclose(observed, expected)
