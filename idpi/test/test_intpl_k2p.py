import os
import shutil
import subprocess

import grib_decoder
import jinja2
import numpy as np
import pytest
import xarray as xr
from operators.vertical_interpolation import interpolate_k2p


@pytest.mark.parametrize("mode", ["nearest_sfc", "linear_in_p", "linear_in_lnp"])
def test_intpl_k2p(mode):
    # define target coordinates
    tc_values = [40.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1100.0]
    fx_voper_lev = "40,500,600,700,800,900,1100"
    tc_units = "hPa"

    # mode dependent tolerances
    atolerances = {"nearest_sfc": 0, "linear_in_p": 1e-5, "linear_in_lnp": 1e-5}
    rtolerances = {"nearest_sfc": 0, "linear_in_p": 1e-7, "linear_in_lnp": 1e-6}

    # mode translation for fieldextra
    fx_modes = {
        "nearest_sfc": "nearest",
        "linear_in_p": "lin_p",
        "linear_in_lnp": "lin_lnp",
    }

    # input data
    datadir = "/project/s83c/rz+/icon_data_processing_incubator/data/SWISS"
    datafile = datadir + "/lfff00000000.ch"

    # fieldextra executable
    executable = "/project/s83c/fieldextra/tsa/bin/fieldextra_gnu_opt_omp"
    # list of diagnostic files produced by fieldextra
    fx_diagnostics = ["fieldextra.diagnostic"]

    # prepare the temporary directory to store rendered fieldextra namelists
    testdir = os.path.dirname(os.path.realpath(__file__))
    tmpdir = testdir + "/tmp"
    cwd = os.getcwd()
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.mkdir(tmpdir)

    # prepare the template generator
    templateLoader = jinja2.FileSystemLoader(searchpath=testdir + "/fe_templates")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template("./test_intpl_k2p.nl")

    # load input data set
    ds = {}
    grib_decoder.load_data(ds, ["T", "P"], datafile, chunk_size=None)

    # call interpolation operator
    T = interpolate_k2p(ds["T"], mode, ds["P"], tc_values, tc_units)

    fx_mode = fx_modes[mode]
    conf_files = {
        "inputi": datadir + "/lfff<DDHH>0000.ch",
        "output": "<HH>_intpl_k2p_" + fx_mode + ".nc",
    }
    fx_out_file = "00_intpl_k2p_" + fx_mode + ".nc"

    rendered_text = template.render(
        file=conf_files, mode=fx_mode, voper_lev=fx_voper_lev
    )
    nl_rendered = os.path.join(tmpdir, "test_intpl_k2p" + fx_mode + ".nl")

    with open(nl_rendered, "w") as nl_file:
        nl_file.write(rendered_text)

    # remove output and diagnostics produced during previous runs of fieldextra
    for afile in [fx_out_file] + fx_diagnostics:
        if os.path.exists(os.path.join(cwd, afile)):
            os.remove(os.path.join(cwd, afile))

    # run fieldextra
    subprocess.run([executable, nl_rendered], check=True)

    fx_ds = xr.open_dataset(fx_out_file)
    t_ref = fx_ds["T"].rename(
        {"x_1": "x", "y_1": "y", "z_1": "isobaricInPa", "epsd_1": "number"}
    )

    # compare numerical results
    assert np.allclose(
        t_ref, T, rtol=rtolerances[mode], atol=atolerances[mode], equal_nan=True
    )


if __name__ == "__main__":
    test_intpl_k2p()
