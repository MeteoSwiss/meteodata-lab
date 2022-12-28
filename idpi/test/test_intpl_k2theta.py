import os
import shutil
import subprocess

import grib_decoder
import jinja2
import numpy as np
import pytest
import xarray as xr
from operators.destagger import destagger
from operators.theta import ftheta
from operators.vertical_interpolation import interpolate_k2theta


@pytest.mark.parametrize("mode", ["high_fold", "low_fold", "undef_fold"])
def test_intpl_k2theta(mode):
    # define target coordinates
    tc_values = [280.0, 290.0, 310.0, 315.0, 320.0, 325.0, 330.0, 335.0]
    fx_voper_lev = "280,290,310,315,320,325,330,335"
    tc_units = "K"

    # mode dependent tolerances
    atolerances = {"undef_fold": 1e-5, "low_fold": 1e-5, "high_fold": 1e-5}
    rtolerances = {"undef_fold": 1e-7, "low_fold": 1e-7, "high_fold": 1e-7}

    # input data
    datadir = "/project/s83c/rz+/icon_data_processing_incubator/data/SWISS"
    datafile = datadir + "/lfff00000000.ch"
    cdatafile = datadir + "/lfff00000000c.ch"

    # fieldextra executable
    fx_executable = "/project/s83c/fieldextra/tsa/bin/fieldextra_gnu_opt_omp"
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
    template = templateEnv.get_template("./test_intpl_k2theta.nl")

    # load input data set
    ds = {}
    grib_decoder.load_data(ds, ["T", "P"], datafile, chunk_size=None)
    grib_decoder.load_data(ds, ["HHL"], cdatafile, chunk_size=None)

    THETA = ftheta(ds["P"], ds["T"])
    HFL = destagger(ds["HHL"], "generalVertical")

    # call interpolation operator
    T = interpolate_k2theta(ds["T"], mode, THETA, tc_values, tc_units, HFL)

    conf_files = {
        "inputi": datadir + "/lfff<DDHH>0000.ch",
        "output": "<HH>_intpl_k2theta_" + mode + ".nc",
    }
    fx_out_file = "00_intpl_k2theta_" + mode + ".nc"

    rendered_text = template.render(
        file=conf_files, mode=mode, voper_lev=fx_voper_lev, voper_lev_units=tc_units
    )
    nl_rendered = os.path.join(tmpdir, "test_intpl_k2theta" + mode + ".nl")

    with open(nl_rendered, "w") as nl_file:
        nl_file.write(rendered_text)

    # remove output and diagnostics produced during previous runs of fieldextra
    for afile in [fx_out_file] + fx_diagnostics:
        if os.path.exists(os.path.join(cwd, afile)):
            os.remove(os.path.join(cwd, afile))

    # run fieldextra
    subprocess.run([fx_executable, nl_rendered], check=True)

    fx_ds = xr.open_dataset(fx_out_file)
    t_ref = fx_ds["T"].rename(
        {"x_1": "x", "y_1": "y", "z_1": "theta", "epsd_1": "number"}
    )

    # compare numerical results
    assert np.allclose(
        t_ref, T, rtol=rtolerances[mode], atol=atolerances[mode], equal_nan=True
    )


if __name__ == "__main__":
    test_intpl_k2theta()
