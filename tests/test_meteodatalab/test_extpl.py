# Third-party
from numpy.testing import assert_allclose

# First-party
import meteodatalab.physical_constants as pc
from meteodatalab import data_source, grib_decoder
from meteodatalab.metadata import override, set_origin_xy
from meteodatalab.operators.destagger import destagger
from meteodatalab.operators.vertical_extrapolation import (
    extrapolate_geopotential_sfc2p,
    extrapolate_temperature_sfc2p,
)
from meteodatalab.operators.vertical_interpolation import interpolate_k2p


def test_extrapolate_sfc2p(data_dir):

    # define target coordinates
    target_p = 850.0

    # input data
    files = [
        data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000",
        data_dir / "COSMO-1E/1h/const/000/lfff00000000c",
    ]

    # load input data set
    fds = data_source.FileDataSource(datafiles=files)
    ds_sfc = grib_decoder.load(fds, {"param": ["HSURF", "T_2M", "PS"]})
    ds_ml = grib_decoder.load(fds, {"param": ["HHL", "T", "P"]})
    set_origin_xy(ds_ml, ref_param="HHL")
    hfl = destagger(ds_ml["HHL"], "z")
    fi = (hfl * pc.g).assign_attrs(override(hfl.attrs["metadata"], shortName="FI"))

    # call extrapolation operator for geopotential
    expected = interpolate_k2p(
        fi, "linear_in_lnp", ds_ml["P"], [target_p], "hPa"
    ).squeeze("z")
    res = (
        extrapolate_geopotential_sfc2p(
            ds_sfc["HSURF"], ds_sfc["T_2M"], ds_sfc["PS"], target_p * 100.0
        )
        .squeeze("z")
        .where(~expected.isnull())
    )
    assert_allclose(res, expected, rtol=0.1)

    # call extrapolation operator for temperature
    expected = interpolate_k2p(
        ds_ml["T"], "linear_in_lnp", ds_ml["P"], [target_p], "hPa"
    ).squeeze("z")
    res = (
        extrapolate_temperature_sfc2p(
            ds_sfc["T_2M"], ds_sfc["HSURF"], ds_sfc["PS"], target_p * 100.0
        )
        .squeeze("z")
        .where(~expected.isnull())
    )
    assert_allclose(res, expected, rtol=0.1)
