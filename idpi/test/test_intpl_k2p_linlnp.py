import os
import shutil
import subprocess

import grib_decoder
import jinja2
import numpy as np
import xarray as xr
from operators.vertical_interpolation import interpolate_k2p


def test_intpl_k2p_linlnp():
    datadir = "/project/s83c/rz+/icon_data_processing_incubator/data/SWISS"
    datafile = datadir + "/lfff00000000.ch"

    ds = {}
    grib_decoder.load_data(ds, ["T", "P"], datafile, chunk_size=None)

    T = interpolate_k2p(ds["T"], "linear_in_lntcf", ds["P"], [40.,500.,600.,700.,800.,1100.], "hPa")

    conf_files = {
        "inputi": datadir + "/lfff<DDHH>0000.ch",
        "output": "<HH>_intpl_k2p_linlnp.nc"
    }
    out_file = "00_intpl_k2p_linlnp.nc"
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
    template = templateEnv.get_template("./test_intpl_k2p_linlnp.nl")
    outputText = template.render(file=conf_files, ready_flags=tmpdir)

    with open(tmpdir + "/test_intpl_k2p_linlnp.nl", "w") as nl_file:
        nl_file.write(outputText)

    # remove output and product files
    for afile in [out_file] + prodfiles:
        if os.path.exists(cwd + "/" + afile):
            os.remove(cwd + "/" + afile)

    subprocess.run([executable, tmpdir + "/test_intpl_k2p_linlnp.nl "], check=True)

    fs_ds = xr.open_dataset("00_intpl_k2p_linlnp.nc")
    t_ref = fs_ds["T"].rename({"x_1": "x", "y_1": "y", "z_1": "isobaricInPa", "epsd_1": "number"})

    assert np.allclose(t_ref, T, rtol=3e-5, atol=5e-2, equal_nan=True)

if __name__ == "__main__":
    test_intpl_k2p_linlnp()
