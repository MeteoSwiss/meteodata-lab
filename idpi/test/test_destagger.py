import os
import shutil
import subprocess

import grib_decoder
import jinja2
import numpy as np
import xarray as xr
from operators.destagger import destagger


def test_destagger():
    datadir = "/project/s83c/rz+/icon_data_processing_incubator/data/SWISS"
    datafile = datadir + "/lfff00000000.ch"
    cdatafile = datadir + "/lfff00000000c.ch"

    ds = {}
    grib_decoder.load_data(ds, ["U", "V"], datafile, chunk_size=None)
    grib_decoder.load_data(ds, ["HHL"], cdatafile, chunk_size=None)

    U = destagger(ds["U"], "x")
    V = destagger(ds["V"], "y")
    HFL = destagger(ds["HHL"], "generalVerticalLayer")

    conf_files = {
        "inputi": datadir + "/lfff<DDHH>0000.ch",
        "inputc": datadir + "/lfff00000000c.ch",
        "output": "<HH>_destagger.nc",
    }
    out_file = "00_destagger.nc"
    prodfiles = ["fieldextra.diagnostic", "fieldextra.product", "fieldextra.rmode"]

    testdir = os.path.dirname(os.path.realpath(__file__))
    tmpdir = testdir + "/tmp"
    cwd = os.getcwd()

    executable = "/project/s83c/fieldextra/tsa/bin/fieldextra_gnu_opt_omp"

    # create the tmp dir
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.mkdir(tmpdir)

    templateLoader = jinja2.FileSystemLoader(searchpath=testdir + "/fe_templates")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template("./test_destagger.nl")
    outputText = template.render(file=conf_files, ready_flags=tmpdir)

    with open(tmpdir + "/test_destagger.nl", "w") as nl_file:
        nl_file.write(outputText)

    # remove output and product files
    for afile in [out_file] + prodfiles:
        if os.path.exists(cwd + "/" + afile):
            os.remove(cwd + "/" + afile)

    subprocess.run([executable, tmpdir + "/test_destagger.nl "], check=True)

    fs_ds = xr.open_dataset("00_destagger.nc")
    u_ref = fs_ds["U"].rename({"x_1": "x", "y_1": "y", "z_1": "generalVerticalLayer"})
    v_ref = fs_ds["V"].rename({"x_1": "x", "y_1": "y", "z_1": "generalVerticalLayer"})
    hfl_ref = fs_ds["HFL"].rename(
        {"x_1": "x", "y_1": "y", "z_1": "generalVerticalLayer"}
    )

    assert np.allclose(u_ref, U, rtol=3e-5, atol=5e-2, equal_nan=True)
    assert np.allclose(v_ref, V, rtol=3e-5, atol=5e-2, equal_nan=True)
    assert np.allclose(hfl_ref, HFL, rtol=3e-3, atol=5e-2, equal_nan=True)


if __name__ == "__main__":
    test_destagger()
