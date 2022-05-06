import os
import shutil
import subprocess

import grib_decoder
import jinja2
import numpy as np
import operators.thetav as mthetav
import xarray as xr


def test_thetav():
    datadir = "/project/s83c/rz+/icon_data_processing_incubator/data/SWISS"
    datafile = datadir + "/lfff00000000.ch"

    ds = {}
    grib_decoder.load_data(ds, ["P", "T", "QV"], datafile, chunk_size=None)

    thetav = mthetav.fthetav(ds["P"], ds["T"], ds["QV"])

    conf_files = {
        "inputi": datadir + "/lfff<DDHH>0000.ch",
        "inputc": datadir + "/lfff00000000c.ch",
        "output": "<HH>_THETAV.nc",
    }
    out_file = "00_THETAV.nc"
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
    template = templateEnv.get_template("./test_THETAV.nl")
    outputText = template.render(file=conf_files, ready_flags=tmpdir)

    with open(tmpdir + "/test_THETAV.nl", "w") as nl_file:
        nl_file.write(outputText)

    # remove output and product files
    for afile in [out_file] + prodfiles:
        if os.path.exists(cwd + "/" + afile):
            os.remove(cwd + "/" + afile)

    subprocess.run([executable, tmpdir + "/test_THETAV.nl "], check=True)

    fs_ds = xr.open_dataset("00_THETAV.nc")

    assert np.allclose(fs_ds["THETA_V"], thetav)


if __name__ == "__main__":
    test_thetav()
