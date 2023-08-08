# Standard library
from pathlib import Path

# Third-party
import numpy as np
import pytest
import xarray as xr
from numpy.testing import assert_allclose

# First-party
from idpi import grib_decoder
from idpi.operators.time_operators import delta


@pytest.fixture
def data_dir():
    return Path("/project/s83c/rz+/icon_data_processing_incubator/data/temporal")


def test_delta(data_dir, fieldextra):
    steps = np.arange(0, 16, 3)
    dd, hh = np.divmod(steps, 24)
    datafiles = [data_dir / f"lfff{d:02d}{h:02d}0000" for d, h in zip(dd, hh)]

    ds = grib_decoder.load_cosmo_data(["TOT_PREC"], datafiles, ref_param="TOT_PREC")

    tot_prec_03h = delta(ds["TOT_PREC"], np.timedelta64(3, "h"))

    # Negative values are replaced by zero as these are due to numerical inaccuracies.
    cond = np.logical_or(tot_prec_03h > 0.0, tot_prec_03h.isnull())
    observed = tot_prec_03h.where(cond, 0.0)

    fx_ds_h = fieldextra(
        "time_ops_delta",
        hh=hh.tolist(),
        conf_files={
            "inputi": data_dir / "lfff<DDHH>0000",
            "inputc": data_dir / "lfff00000000c",
            "output": "<HH>_time_ops_delta.nc",
        },
    )

    expected = xr.concat([fx_ds["tot_prec_03h"] for fx_ds in fx_ds_h], dim="time")

    assert_allclose(observed, expected.transpose("epsd_1", "time", ...))
