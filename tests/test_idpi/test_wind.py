# Third-party
from numpy.testing import assert_allclose

# First-party
from idpi.grib_decoder import GribReader
from idpi.metadata import set_origin_xy
from idpi.operators import wind


def test_wind(data_dir, fieldextra):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    reader = GribReader.from_files([datafile, cdatafile])
    ds = reader.load_fieldnames(["U_10M", "V_10M"])
    set_origin_xy(ds, ref_param="U_10M")

    u_10m = ds["U_10M"].isel(z=0)
    v_10m = ds["V_10M"].isel(z=0)

    ff_10m = wind.speed(u_10m, v_10m)
    dd_10m = wind.direction(u_10m, v_10m)

    fx_ds = fieldextra("wind")

    assert_allclose(ff_10m, fx_ds["FF_10M"], rtol=1e-6)
    assert_allclose(dd_10m, fx_ds["DD_10M"], atol=1e-4)

    assert ff_10m.parameter == {
        "centre": "lssw",
        "name": "Wind speed (SP_10M)",
        "paramId": 500025,
        "shortName": "SP_10M",
        "units": "m s-1",
    }

    assert dd_10m.parameter == {
        "centre": "lssw",
        "name": "Wind Direction (DD_10M)",
        "paramId": 500023,
        "shortName": "DD_10M",
        "units": "degree true",
    }
