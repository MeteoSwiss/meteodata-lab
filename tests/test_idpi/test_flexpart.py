# Standard library
import os
import pathlib
import shutil
import subprocess

# Third-party
import eccodes  # type: ignore
import jinja2
import numpy as np
import pytest
import xarray as xr

# First-party
import idpi.operators.flexpart as flx
from idpi.system_definition import root_dir


@pytest.mark.ifs
def test_flexpart():
    gpaths = os.environ["GRIB_DEFINITION_PATH"].split(":")
    eccodes_gpath = [p for p in gpaths if "eccodes-cosmo-resources" not in p][0]
    eccodes.codes_set_definitions_path(eccodes_gpath)

    datadir = "/project/s83c/rz+/icon_data_processing_incubator/data/flexpart/"
    datafile = datadir + "/efsf00000000"
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
        (pathlib.Path(root_dir) / ".." / "share" / "field_mappings.yml").resolve()
    )
    ds = flx.load_flexpart_data(constants + inputf, loader, datafile)

    for h in range(3, 10, 3):
        datafile = datadir + f"/efsf00{h:02d}0000"
        newds = flx.load_flexpart_data(inputf, loader, datafile)

        for field in newds:
            ds[field] = xr.concat([ds[field], newds[field]], dim="step")

    conf_files = {
        "inputi": datadir + "/efsf00<HH>0000",
        "inputc": datadir + "/efsf00000000",
        "output": "<HH>_flexpart.nc",
    }
    out_file = "00_flexpart.nc"
    prodfiles = ["fieldextra.diagnostic"]

    testdir = os.path.dirname(os.path.realpath(__file__))
    tmpdir = testdir + "/tmp"
    cwd = os.getcwd()

    executable = "/project/s83c/fieldextra/tsa/bin/fieldextra_gnu_opt_omp"

    # create the tmp dir
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.mkdir(tmpdir)

    templateLoader = jinja2.FileSystemLoader(
        searchpath=testdir + "/fieldextra_templates"
    )
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template("./test_flexpart.nl")
    outputText = template.render(file=conf_files, ready_flags=tmpdir)

    with open(tmpdir + "/test_flexpart.nl", "w") as nl_file:
        nl_file.write(outputText)

    # remove output and product files
    for afile in [out_file] + prodfiles:
        if os.path.exists(cwd + "/" + afile):
            os.remove(cwd + "/" + afile)

    subprocess.run([executable, tmpdir + "/test_flexpart.nl "], check=True)

    fs_ds = xr.open_dataset("00_flexpart.nc")
    fs_ds_o = {}
    for f in ("FIS", "FR_LAND", "SDOR"):
        fs_ds_o[f] = fs_ds[f].isel(y_1=slice(None, None, -1))

    ds_out = {}
    for field in ("FIS", "FR_LAND", "SDOR"):
        ds_out[field] = ds[field]

    assert np.allclose(fs_ds_o["FIS"], ds["FIS"], rtol=3e-7, atol=5e-7, equal_nan=True)
    assert np.allclose(
        fs_ds_o["FR_LAND"], ds["FR_LAND"], rtol=3e-7, atol=5e-7, equal_nan=True
    )
    assert np.allclose(
        fs_ds_o["SDOR"], ds["SDOR"], rtol=3e-7, atol=5e-7, equal_nan=True
    )

    # Compute few steps of a 3 hourly data
    for i in range(1, 2):
        h = i * 3

        fs_ds = xr.open_dataset(f"{h:02d}_flexpart.nc")
        fs_ds_o = dict()

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

        ds_out = flx.fflexpart(ds, i)

        assert np.allclose(
            fs_ds_o["ETADOT"].transpose("y_1", "x_1", "z_1", "time").isel(time=0),
            ds_out["OMEGA"],
            rtol=3e-6,
            atol=5e-5,
            equal_nan=True,
        )
        assert np.allclose(
            fs_ds_o["U"], ds_out["U"], rtol=3e-7, atol=5e-7, equal_nan=True
        )
        assert np.allclose(
            fs_ds_o["V"], ds_out["V"], rtol=3e-7, atol=5e-7, equal_nan=True
        )
        assert np.allclose(
            fs_ds_o["T"], ds_out["T"], rtol=3e-7, atol=5e-7, equal_nan=True
        )
        assert np.allclose(
            fs_ds_o["QV"], ds_out["QV"], rtol=3e-7, atol=5e-7, equal_nan=True
        )
        assert np.allclose(
            fs_ds_o["PS"], ds_out["PS"], rtol=3e-7, atol=5e-7, equal_nan=True
        )
        assert np.allclose(
            fs_ds_o["U_10M"], ds_out["U_10M"], rtol=3e-7, atol=5e-7, equal_nan=True
        )
        assert np.allclose(
            fs_ds_o["V_10M"], ds_out["V_10M"], rtol=3e-7, atol=5e-7, equal_nan=True
        )
        assert np.allclose(
            fs_ds_o["T_2M"], ds_out["T_2M"], rtol=3e-7, atol=5e-7, equal_nan=True
        )
        assert np.allclose(
            fs_ds_o["TD_2M"], ds_out["TD_2M"], rtol=3e-7, atol=5e-7, equal_nan=True
        )
        assert np.allclose(
            fs_ds_o["CLCT"], ds_out["CLCT"], rtol=3e-7, atol=5e-7, equal_nan=True
        )
        assert np.allclose(
            fs_ds_o["W_SNOW"], ds_out["W_SNOW"], rtol=3e-7, atol=5e-7, equal_nan=True
        )

        assert np.allclose(
            fs_ds_o["TOT_CON"], ds_out["TOT_CON"], rtol=3e-6, atol=5e-7, equal_nan=True
        )
        assert np.allclose(
            fs_ds_o["TOT_GSP"], ds_out["TOT_GSP"], rtol=3e-6, atol=5e-7, equal_nan=True
        )
        assert np.allclose(
            fs_ds_o["SSR"], ds_out["ASOB_S"], rtol=3e-7, atol=5e-7, equal_nan=True
        )
        assert np.allclose(
            fs_ds_o["SSHF"], ds_out["ASHFL_S"], rtol=3e-7, atol=5e-7, equal_nan=True
        )
        assert np.allclose(
            fs_ds_o["EWSS"], ds_out["EWSS"], rtol=3e-7, atol=5e-7, equal_nan=True
        )


if __name__ == "__main__":
    test_flexpart()
