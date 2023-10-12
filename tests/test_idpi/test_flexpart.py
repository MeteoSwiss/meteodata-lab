# Standard library
from pathlib import Path

# Third-party
import pytest
import xarray as xr
from numpy.testing import assert_allclose

# First-party
import idpi.config
import idpi.operators.flexpart as flx
from idpi.grib_decoder import GribReader


@pytest.fixture
def data_dir(data_dir):
    return Path("/project/s83c/rz+/icon_data_processing_incubator/data/flexpart/")


@pytest.mark.ifs
def test_flexpart(data_dir, fieldextra):
    datafiles = list(data_dir.glob("efs*"))
    constants = ("z", "lsm", "sdor")
    inputf = (
        "etadot",
        "t",
        "q",
        "u",
        "v",
        "sp",
        "10u",
        "10v",
        "2t",
        "2d",
        "tcc",
        "sd",
        "cp",
        "lsp",
        "ssr",
        "sshf",
        "ewss",
        "nsss",
    )

    with idpi.config.set_values(data_scope="ifs"):
        reader = GribReader(datafiles, ref_param="t")
        ds = reader.load_fields(inputf + constants, extract_pv="u")

    conf_files = {
        "inputi": str(data_dir / "efsf00<HH>0000"),
        "inputc": str(data_dir / "efsf00000000"),
        "output": "<HH>_flexpart.nc",
    }

    fs_ds, *fs_ds_h = fieldextra("flexpart", hh=(0, 3, 6), conf_files=conf_files)
    fs_ds_o = {}
    for f in ("FIS", "FR_LAND", "SDOR"):
        fs_ds_o[f] = fs_ds[f].isel(y_1=slice(None, None, -1))

    assert_allclose(fs_ds_o["FIS"], ds["z"].squeeze(), rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["FR_LAND"], ds["lsm"].squeeze(), rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["SDOR"], ds["sdor"].squeeze(), rtol=3e-7, atol=5e-7)

    for field in (
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
        "NSSS",
        "ETADOT",
    ):
        fs_ds_o[field] = xr.concat([ds[field] for ds in fs_ds_h], dim="time").isel(
            y_1=slice(None, None, -1)
        )

    ds_out = flx.fflexpart(
        {
            param: field.isel(time=slice(3), missing_dims="ignore")
            for param, field in ds.items()
        }
    )

    assert_allclose(fs_ds_o["ETADOT"], ds_out["omega"], rtol=3e-6, atol=5e-5)
    assert_allclose(fs_ds_o["U"], ds_out["u"], rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["V"], ds_out["v"], rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["T"], ds_out["t"], rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["QV"], ds_out["q"], rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["PS"], ds_out["sp"], rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["U_10M"], ds_out["10u"], rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["V_10M"], ds_out["10v"], rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["T_2M"], ds_out["2t"], rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["TD_2M"], ds_out["2d"], rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["CLCT"], ds_out["tcc"], rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["W_SNOW"], ds_out["sd"], rtol=3e-7, atol=5e-7)

    assert_allclose(fs_ds_o["TOT_CON"], ds_out["cp"] * 1000, rtol=3e-6, atol=5e-7)
    assert_allclose(fs_ds_o["TOT_GSP"], ds_out["lsp"] * 1000, rtol=3e-6, atol=5e-7)
    assert_allclose(fs_ds_o["SSR"], ds_out["ssr"], rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["SSHF"], ds_out["sshf"], rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["EWSS"], ds_out["ewss"], rtol=3e-7, atol=5e-7)
    assert_allclose(fs_ds_o["NSSS"], ds_out["nsss"], rtol=3e-7, atol=5e-7)
