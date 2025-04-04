# Third-party
import numpy as np
import pandas as pd  # type: ignore
import pytest
import xarray as xr
from numpy.testing import assert_allclose

# First-party
import meteodatalab.operators.time_operators as time_ops
from meteodatalab.grib_decoder import GribReader
from meteodatalab.operators import radiation


def _assert_keys(field, mapping):
    for key, value in mapping.items():
        assert field.metadata.get(key) == value


@pytest.mark.data("reduced-time")
def test_delta(data_dir, fieldextra):
    steps = np.arange(34)
    dd, hh = np.divmod(steps, 24)
    datafiles = [data_dir / f"lfff{d:02d}{h:02d}0000" for d, h in zip(dd, hh)]

    reader = GribReader.from_files(datafiles)
    ds = reader.load_fieldnames(["TOT_PREC"])

    tot_prec = time_ops.resample(ds["TOT_PREC"], np.timedelta64(3, "h"))
    tot_prec_03h = time_ops.delta(tot_prec, np.timedelta64(3, "h"))

    # Negative values are replaced by zero as these are due to numerical inaccuracies.
    cond = np.logical_or(tot_prec_03h > 0.0, tot_prec_03h.isnull())
    observed = tot_prec_03h.where(cond, 0.0)

    fx_ds_h = fieldextra(
        "time_ops_delta",
        load_output=[f"{i:02d}_time_ops_delta.nc" for i in steps[::3]],
        conf_files={
            "inputi": data_dir / "lfff<DDHH>0000",
            "inputc": data_dir / "lfff00000000c",
            "output": "<HH>_time_ops_delta.nc",
        },
    )

    expected = xr.concat(
        [fx_ds["tot_prec_03h"] for fx_ds in fx_ds_h], dim="time"
    ).transpose("epsd_1", "ref_time", "time", ...)

    assert_allclose(observed, expected)

    md = {
        "typeOfStatisticalProcessing": 4,
        "indicatorOfUnitForTimeRange": 0,
        "lengthOfTimeRange": 3 * 60,
    }
    _assert_keys(observed, md)


@pytest.mark.data("reduced-time")
def test_resample_average(data_dir, fieldextra):
    steps = np.arange(12)
    dd, hh = np.divmod(steps, 24)
    datafiles = [data_dir / f"lfff{d:02d}{h:02d}0000" for d, h in zip(dd, hh)]

    reader = GribReader.from_files(datafiles)
    ds = reader.load_fieldnames(["ASWDIFD_S", "ASWDIR_S"])

    direct = time_ops.resample_average(ds["ASWDIR_S"], np.timedelta64(1, "h"))
    diffuse = time_ops.resample_average(ds["ASWDIFD_S"], np.timedelta64(1, "h"))

    observed = radiation.compute_swdown(diffuse, direct)

    assert observed.parameter == {
        "centre": "lssw",
        "paramId": 503174,
        "shortName": "ASOD_S",
        "units": "W m-2",
        "name": "Downward short wave radiation flux at surface (time average)",
    }

    fx_ds_h = fieldextra(
        "time_ops_tdelta",
        load_output=[f"{i:02d}_time_ops_tdelta.nc" for i in steps],
        conf_files={
            "inputi": data_dir / "lfff<DDHH>0000",
            "inputc": data_dir / "lfff00000000c",
            "output": "<HH>_time_ops_tdelta.nc",
        },
    )

    expected = xr.concat([fx_ds["GLOB"] for fx_ds in fx_ds_h], dim="time").transpose(
        "epsd_1", "ref_time", "time", ...
    )

    assert_allclose(
        observed,
        expected,
        rtol=1e-5,
        atol=1e-5,
    )

    md = {
        "typeOfStatisticalProcessing": 0,
        "indicatorOfUnitForTimeRange": 0,
        "lengthOfTimeRange": 60,
    }
    _assert_keys(observed, md)


@pytest.mark.data("reduced-time")
def test_max(data_dir, fieldextra):
    steps = np.arange(34)
    dd, hh = np.divmod(steps, 24)
    datafiles = [data_dir / f"lfff{d:02d}{h:02d}0000" for d, h in zip(dd, hh)]
    reader = GribReader.from_files(datafiles)
    ds = reader.load_fieldnames(["VMAX_10M"])

    f = ds["VMAX_10M"]
    nsteps = time_ops.get_nsteps(f.valid_time, np.timedelta64(24, "h"))
    zero = np.timedelta64(0, "h")
    vmax_10m_24h = f.where(f.lead_time > zero).rolling(lead_time=nsteps).max()

    # Negative values are replaced by zero as these are due to numerical inaccuracies.
    cond = np.logical_or(vmax_10m_24h > 0.0, vmax_10m_24h.isnull())
    idx = pd.to_timedelta(steps[::3], "h")
    observed = vmax_10m_24h.where(cond, 0.0).sel(lead_time=idx, z=10)

    fx_ds_h = fieldextra(
        "time_ops_max",
        load_output=[f"{i:02d}_time_ops_max.nc" for i in steps[::3]],
        conf_files={
            "inputi": data_dir / "lfff<DDHH>0000",
            "inputc": data_dir / "lfff00000000c",
            "output": "<HH>_time_ops_max.nc",
        },
    )

    expected = xr.concat(
        [fx_ds["vmax_10m_24h"] for fx_ds in fx_ds_h], dim="time"
    ).transpose("epsd_1", "ref_time", "time", ...)

    assert_allclose(observed, expected)


def test_get_nsteps():
    values = pd.date_range("2000-01-01", freq="1h", periods=10)
    valid_time = xr.DataArray(values, dims=["lead_time"])
    assert time_ops.get_nsteps(valid_time, np.timedelta64(5, "h")) == 5


def test_get_nsteps_raises_non_uniform():
    values = pd.date_range("2000-01-01", freq="1h", periods=10)
    valid_time = xr.DataArray(values[[0, 1, 3]], dims=["lead_time"])
    with pytest.raises(ValueError):
        time_ops.get_nsteps(valid_time, np.timedelta64(3, "h"))


def test_get_nsteps_raises_non_multiple():
    values = pd.date_range("2000-01-01", freq="2h", periods=10)
    valid_time = xr.DataArray(values, dims=["lead_time"])
    with pytest.raises(ValueError):
        time_ops.get_nsteps(valid_time, np.timedelta64(3, "h"))
