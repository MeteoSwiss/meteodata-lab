# Third-party
from numpy.testing import assert_allclose

# First-party
import meteodatalab.physical_constants as pc
from meteodatalab import data_source, grib_decoder
from meteodatalab.metadata import override, set_origin_xy
from meteodatalab.operators.destagger import destagger
from meteodatalab.operators.vertical_extrapolation import (
    extrapolate_geopotential_sfc2p,
    extrapolate_k2p,
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
    ds = grib_decoder.load(fds, {"param": ["HSURF", "T_2M", "PS", "HHL", "T", "P"]})
    set_origin_xy(ds, ref_param="HHL")
    hfl = destagger(ds["HHL"], "z")
    fi = (hfl * pc.g).assign_attrs(override(hfl.attrs["metadata"], shortName="FI"))

    # call extrapolation operator for geopotential
    expected = interpolate_k2p(fi, "linear_in_lnp", ds["P"], [target_p], "hPa").squeeze(
        "z"
    )
    res = (
        extrapolate_geopotential_sfc2p(
            ds["HSURF"], ds["T_2M"], ds["PS"], target_p * 100.0
        )
        .squeeze("z")
        .where(~expected.isnull())
    )
    assert_allclose(res, expected, rtol=0.04)

    # call extrapolation operator for temperature
    expected = interpolate_k2p(
        ds["T"], "linear_in_lnp", ds["P"], [target_p], "hPa"
    ).squeeze("z")
    res = (
        extrapolate_temperature_sfc2p(
            ds["T_2M"], ds["HSURF"], ds["PS"], target_p * 100.0
        )
        .squeeze("z")
        .where(~expected.isnull())
    )
    assert_allclose(res, expected, rtol=0.04)


def test_extrapolate_k2p(data_dir):

    # define target coordinates
    target_p = 850.0

    # input data
    files = [
        str(data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"),
    ]

    # load input data set
    fds = data_source.FileDataSource(datafiles=files)
    ds = grib_decoder.load(fds, {"param": ["QV"]})

    # call extrapolation operator
    expected = ds["QV"][{"z": -1}]
    res = extrapolate_k2p(ds["QV"], target_p * 100.0).squeeze("z")

    assert_allclose(res, expected)
    assert res.metadata.get("typeOfLevel") == "isobaricInPa"
