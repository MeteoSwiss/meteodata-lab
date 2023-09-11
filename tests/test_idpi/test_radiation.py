# Standard library
from pathlib import Path

# Third-party
import numpy as np
import pytest
from numpy.testing import assert_allclose

# First-party
from idpi import grib_decoder
from idpi.operators import radiation
from idpi.operators import time_operators as time_ops


@pytest.fixture
def data_dir():
    return Path("/project/s83c/rz+/icon_data_processing_incubator/data/temporal")


def test_athd_s(data_dir, fieldextra):
    steps = np.arange(34)
    dd, hh = np.divmod(steps, 24)
    datafiles = [data_dir / f"lfff{d:02d}{h:02d}0000" for d, h in zip(dd, hh)]

    reader = grib_decoder.GribReader(datafiles, ref_param="T_G")
    ds = reader.load_cosmo_data(["ATHB_S", "T_G"])

    athb_s = time_ops.resample_average(ds["ATHB_S"], np.timedelta64(1, "h"))
    observed = radiation.compute_athd_s(athb_s, ds["T_G"])

    conf_files = {
        "inputi": data_dir / "lfff<DDHH>0000",
        "output": "athd_s.nc",
    }
    fx_ds = fieldextra("athd_s", conf_files=conf_files, hh=None)
    expected = fx_ds["ATHD_S_TG"].transpose("epsd_1", "time", ...)

    assert_allclose(observed, expected, rtol=1e-6, atol=1e-4)
