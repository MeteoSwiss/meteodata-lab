# Standard library
from importlib.resources import files
from pathlib import Path

# Third-party
import pytest
import xarray as xr
from numpy.testing import assert_allclose

# First-party
import idpi.operators.flexpart as flx


@pytest.fixture
def data_dir(data_dir):
    return Path("/project/s83c/rz+/icon_data_processing_incubator/data/flexpart/")


@pytest.mark.ifs
def test_flexpart(data_dir, fieldextra):
    datafile = data_dir / "efsf00000000"
    constants = ("FIS", "FR_LAND", "SDOR")
    inputf = (
        "ETADOT",
        "T",
        "QV",
        "U",
        "V",
        "PS",
        "U_10M",
        "V_10M",
        "T_2M",
        "TD_2M",
        "CLCT",
        "W_SNOW",
        "TOT_CON",
        "TOT_GSP",
        "ASOB_S",
        "ASHFL_S",
        "EWSS",
        "NSSS",
    )

    loader = flx.ifs_data_loader(
        files("idpi.data").joinpath("field_mappings.yml").open()
    )
    ds = flx.load_flexpart_data(constants + inputf, loader, datafile)

    for h in 3, 6, 9:
        datafile = data_dir / f"efsf00{h:02d}0000"
        newds = flx.load_flexpart_data(inputf, loader, datafile)

        for field in newds:
            ds[field] = xr.concat([ds[field], newds[field]], dim="step")

    conf_files = {
        "inputi": str(data_dir / "efsf00<HH>0000"),
        "inputc": str(data_dir / "efsf00000000"),
        "output": "<HH>_flexpart.nc",
    }

    fs_ds, *fs_ds_h = fieldextra("flexpart", hh=(0, 3, 6), conf_files=conf_files)
    fs_ds_o = {}
    for f in ("FIS", "FR_LAND", "SDOR"):
        fs_ds_o[f] = fs_ds[f].isel(y_1=slice(None, None, -1))

    assert_allclose(fs_ds_o["FIS"], ds["FIS"], rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["FR_LAND"], ds["FR_LAND"], rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["SDOR"], ds["SDOR"], rtol=3e-7, atol=5e-7)

    # Compute few steps of a 3 hourly data
    steps = 1, 2
    for step, fs_ds in zip(steps, fs_ds_h):
        fs_ds_o = {}

        # Invert the latitude order in FX netcdf
        for f in (
            "U",
            "V",
            "T",
            "QV",
            "PS",
            "U_10M",
            "V_10M",
            "T_2M",
            "TD_2M",
            "CLCT",
            "W_SNOW",
            "TOT_CON",
            "TOT_GSP",
            "SSR",
            "SSHF",
            "EWSS",
            "ETADOT",
        ):
            fs_ds_o[f] = fs_ds[f].isel(y_1=slice(None, None, -1))

        ds_out = flx.fflexpart(ds, step)

        assert_allclose(
            fs_ds_o["ETADOT"].transpose("y_1", "x_1", "z_1", "time").isel(time=0),
            ds_out["OMEGA"],
            rtol=3e-6,
            atol=5e-5,
        )
        assert_allclose(fs_ds_o["U"], ds_out["U"], rtol=3e-7, atol=5e-7)
        assert_allclose(fs_ds_o["V"], ds_out["V"], rtol=3e-7, atol=5e-7)
        assert_allclose(fs_ds_o["T"], ds_out["T"], rtol=3e-7, atol=5e-7)
        assert_allclose(fs_ds_o["QV"], ds_out["QV"], rtol=3e-7, atol=5e-7)
        assert_allclose(fs_ds_o["PS"], ds_out["PS"], rtol=3e-7, atol=5e-7)
        assert_allclose(fs_ds_o["U_10M"], ds_out["U_10M"], rtol=3e-7, atol=5e-7)
        assert_allclose(fs_ds_o["V_10M"], ds_out["V_10M"], rtol=3e-7, atol=5e-7)
        assert_allclose(fs_ds_o["T_2M"], ds_out["T_2M"], rtol=3e-7, atol=5e-7)
        assert_allclose(fs_ds_o["TD_2M"], ds_out["TD_2M"], rtol=3e-7, atol=5e-7)
        assert_allclose(fs_ds_o["CLCT"], ds_out["CLCT"], rtol=3e-7, atol=5e-7)
        assert_allclose(fs_ds_o["W_SNOW"], ds_out["W_SNOW"], rtol=3e-7, atol=5e-7)

        assert_allclose(fs_ds_o["TOT_CON"], ds_out["TOT_CON"], rtol=3e-6, atol=5e-7)
        assert_allclose(fs_ds_o["TOT_GSP"], ds_out["TOT_GSP"], rtol=3e-6, atol=5e-7)
        assert_allclose(fs_ds_o["SSR"], ds_out["ASOB_S"], rtol=3e-7, atol=5e-7)
        assert_allclose(fs_ds_o["SSHF"], ds_out["ASHFL_S"], rtol=3e-7, atol=5e-7)
        assert_allclose(fs_ds_o["EWSS"], ds_out["EWSS"], rtol=3e-7, atol=5e-7)
