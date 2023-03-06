import os
import shutil
import subprocess

import grib_decoder
import jinja2
import numpy as np
import pytest
import xarray as xr
from operators.destagger import destagger
from operators.vertical_reduction import minmax_k


@pytest.mark.parametrize("operator", ["maximum", "minimum"])
@pytest.mark.parametrize("field", ["T", "W"])
def test_minmax_z2z(operator, field):

    # modes
    mode = "z2z"

    # k indices defining h_bounds (count starting with 1)
    k_bottom = 61
    k_top = 60

    # operator dependent tolerances
    atolerances = {"maximum": 1e-5, "minimum": 1e-5}
    rtolerances = {"maximum": 1e-6, "minimum": 1e-6}

    # operator translation for fieldextra
    fx_operators = {
        "maximum": "max",
        "minimum": "min",
    }

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

    # load input data set
    ds = {}
    grib_decoder.load_data(ds, field, datafile, chunk_size=None)
    grib_decoder.load_data(ds, ["HHL"], cdatafile, chunk_size=None)
    HHL = ds["HHL"]
    HFL = destagger(HHL, "generalVertical")
    # ATTENTION: attributes are lost in destagger operation

    if "generalVerticalLayer" in ds[field].coords:
        height = HFL
        h_bounds = [
            height.isel(generalVerticalLayer=k_bottom - 1),
            height.isel(generalVerticalLayer=k_top - 1),
        ]
        template = templateEnv.get_template("./test_minmax_z2z_for_h_k_full.nl")
    elif "generalVertical" in ds[field].coords:
        height = HHL
        h_bounds = [
            height.isel(generalVertical=k_bottom - 1),
            height.isel(generalVertical=k_top - 1),
        ]
        template = templateEnv.get_template("./test_minmax_z2z_for_h_k_half.nl")
    else:
        raise RuntimeError(
            "type of vertical coordinates for field ", field, " is not supported"
        )

    # call reduction operator
    f_minmax = minmax_k(ds[field], operator, mode, height, h_bounds)

    conf_files = {
        "inputc": datadir + "/lfff00000000c.ch",
        "inputi": datadir + "/lfff<DDHH>0000.ch",
        "output": "<HH>_" + fx_operators[operator] + "_" + mode + ".nc",
    }
    fx_out_file = "00_" + fx_operators[operator] + "_" + mode + ".nc"

    rendered_text = template.render(
        file=conf_files,
        minmax=fx_operators[operator],
        field=field,
        mode=mode,
        kbottom=k_bottom,
        ktop=k_top,
    )
    nl_rendered = os.path.join(tmpdir, "test_minmax_" + mode + ".nl")

    with open(nl_rendered, "w") as nl_file:
        nl_file.write(rendered_text)

    # remove output and diagnostics produced during previous runs of fieldextra
    for afile in [fx_out_file] + fx_diagnostics:
        if os.path.exists(os.path.join(cwd, afile)):
            os.remove(os.path.join(cwd, afile))

    # run fieldextra
    subprocess.run([fx_executable, nl_rendered], check=True)

    fx_ds = xr.open_dataset(fx_out_file)
    f_minmax_ref = fx_ds[field].rename({"x_1": "x", "y_1": "y", "epsd_1": "number"})

    # compare numerical results
    assert np.allclose(
        f_minmax_ref,
        f_minmax,
        rtol=rtolerances[operator],
        atol=atolerances[operator],
        equal_nan=True,
    )


if __name__ == "__main__":
    test_minmax_z2z()
