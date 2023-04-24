# Standard library
import os
import shutil
import subprocess

# Third-party
import jinja2
import numpy as np
import xarray as xr

# First-party
import idpi.operators.brn as mbrn
from idpi import grib_decoder
from idpi.system_definition import FX_BINARY
from idpi.system_definition import INPUT_DATA_DIR


def test_brn():
    datafile = INPUT_DATA_DIR + "/lfff00000000.ch"
    cdatafile = INPUT_DATA_DIR + "/lfff00000000c.ch"

    ds = {}
    grib_decoder.load_data(ds, ["P", "T", "QV", "U", "V"], datafile, chunk_size=None)
    grib_decoder.load_data(ds, ["HHL", "HSURF"], cdatafile, chunk_size=None)

    brn = mbrn.fbrn(
        ds["P"], ds["T"], ds["QV"], ds["U"], ds["V"], ds["HHL"], ds["HSURF"]
    )

    conf_files = {
        "inputi": INPUT_DATA_DIR + "/lfff<DDHH>0000.ch",
        "inputc": INPUT_DATA_DIR + "/lfff00000000c.ch",
        "output": "<HH>_BRN.nc",
    }
    out_file = "00_BRN.nc"
    prodfiles = ["fieldextra.diagnostic"]

    testdir = os.path.dirname(os.path.realpath(__file__))
    tmpdir = testdir + "/tmp"
    cwd = os.getcwd()

    # create the tmp dir
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.mkdir(tmpdir)

    templateLoader = jinja2.FileSystemLoader(
        searchpath=testdir + "/fieldextra_templates"
    )
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template("./test_BRN.nl")
    outputText = template.render(file=conf_files, ready_flags=tmpdir)

    with open(tmpdir + "/test_BRN.nl", "w") as nl_file:
        nl_file.write(outputText)

    # remove output and product files
    for afile in [out_file] + prodfiles:
        if os.path.exists(cwd + "/" + afile):
            os.remove(cwd + "/" + afile)

    subprocess.run([FX_BINARY, tmpdir + "/test_BRN.nl "], check=True)

    fs_ds = xr.open_dataset("00_BRN.nc")
    brn_ref = fs_ds["BRN"].rename(
        {"x_1": "x", "y_1": "y", "z_1": "generalVerticalLayer"}
    )
    assert np.allclose(brn_ref, brn, rtol=5e-3, atol=5e-2, equal_nan=True)


if __name__ == "__main__":
    test_brn()
