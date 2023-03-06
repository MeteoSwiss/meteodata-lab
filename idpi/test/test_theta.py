import os
import shutil
import subprocess

import grib_decoder
import jinja2
import numpy as np
import operators.theta as mtheta
import xarray as xr


def test_theta():
    datadir = "/project/s83c/rz+/icon_data_processing_incubator/data/SWISS"
    datafile = datadir + "/lfff00000000.ch"

    ds = {}
    grib_decoder.load_data(ds, ["P", "T"], datafile, chunk_size=None)

    theta = mtheta.ftheta(ds["P"], ds["T"])

    conf_files = {
        "inputi": datadir + "/lfff<DDHH>0000.ch",
        "inputc": datadir + "/lfff00000000c.ch",
        "output": "<HH>_THETA.nc",
    }
    out_file = "00_THETA.nc"
    prodfiles = ["fieldextra.diagnostic"]

    testdir = os.path.dirname(os.path.realpath(__file__))
    tmpdir = testdir + "/tmp"
    cwd = os.getcwd()

    executable = "/project/s83c/fieldextra/tsa/bin/fieldextra_gnu_opt_omp"

    # create the tmp dir
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.mkdir(tmpdir)

    templateLoader = jinja2.FileSystemLoader(searchpath=testdir + "/fe_templates")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template("./test_THETA.nl")
    outputText = template.render(file=conf_files, ready_flags=tmpdir)

    with open(tmpdir + "/test_THETA.nl", "w") as nl_file:
        nl_file.write(outputText)

    # remove output and product files
    for afile in [out_file] + prodfiles:
        if os.path.exists(cwd + "/" + afile):
            os.remove(cwd + "/" + afile)

    subprocess.run([executable, tmpdir + "/test_THETA.nl "], check=True)

    fs_ds = xr.open_dataset("00_THETA.nc")

    assert np.allclose(fs_ds["THETA"], theta)


if __name__ == "__main__":
    test_theta()
