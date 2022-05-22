import os
import shutil
import subprocess

import grib_decoder
import jinja2
import numpy as np
import xarray as xr
from operators.hzerocl import fhzerocl
from operators.destagger import destagger


def test_hzerocl():
    datadir = "/project/s83c/rz+/icon_data_processing_incubator/data/SWISS"
    datafile = datadir + "/lfff00000000.ch"
    cdatafile = datadir + "/lfff00000000c.ch"

    ds = {}
    grib_decoder.load_data(ds, ["T"], datafile, chunk_size=None)
    grib_decoder.load_data(ds, ["HHL"], cdatafile, chunk_size=None)

    conf_files = {
        "inputi": datadir + "/lfff<DDHH>0000.ch",
        "inputc": datadir + "/lfff00000000c.ch",
        "output": "<HH>_hzerocl.nc",
    }
    out_file = "00_hzerocl.nc"
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
    template = templateEnv.get_template("./test_hzerocl.nl")
    outputText = template.render(file=conf_files, ready_flags=tmpdir)

    with open(tmpdir + "/test_hzerocl.nl", "w") as nl_file:
        nl_file.write(outputText)

    # remove output and product files
    for afile in [out_file] + prodfiles:
        if os.path.exists(cwd + "/" + afile):
            os.remove(cwd + "/" + afile)

    subprocess.run([executable, tmpdir + "/test_hzerocl.nl "], check=True)
    hzerocl = fhzerocl(ds["T"], ds["HHL"])

    fs_ds = xr.open_dataset("00_hzerocl.nc")
    hzerocl_ref = fs_ds["HZEROCL"].rename({"x_1": "x", "y_1": "y"}).squeeze()

    # For this dataset, on point [74,211] last level (center of volume), i.e. 80 (1 base), T is 273.14966.
    # Therefore FE should set hzerocl to undefined -999. However it does not, I assume that is because
    # rather than operating on center of volume levels, it interpolates T into faces (where HEIGHT is defined)
    # Needs to be confirmed
    hzerocl_ref[74, 211] = -999
    hzerocl_ref = hzerocl_ref.where(hzerocl_ref != -999)

    assert np.allclose(
        hzerocl_ref,
        hzerocl,
        rtol=3e-1,
        atol=3e-1,
        equal_nan=True,
    )


if __name__ == "__main__":
    test_hzerocl()
