# Third-party
import pytest
from numpy.testing import assert_allclose

# First-party
from meteodatalab.data_source import FileDataSource
from meteodatalab.grib_decoder import load
from meteodatalab.operators.destagger import destagger
from meteodatalab.operators.vertical_interpolation import (
    TargetCoordinates,
    TargetCoordinatesAttrs,
    interpolate_k2any,
)


@pytest.mark.data("original")
def test_intpl_k2any(data_dir, fieldextra):
    # define target coordinates
    tc = TargetCoordinates(
        type_of_level="echoTopInDBZ",
        values=[15.0, 10.0],
        attrs=TargetCoordinatesAttrs(
            standard_name="",
            long_name="radar reflectivity",
            units="dBZ",
            positive="up",
        ),
    )

    # input data
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    # load input data set
    source = FileDataSource(datafiles=[str(datafile), str(cdatafile)])
    ds = load(source, {"param": ["DBZ", "HHL"]})

    hfl = destagger(ds["HHL"].squeeze(drop=True), "z")

    # call interpolation operator
    echo_top = interpolate_k2any(hfl, "high_fold", ds["DBZ"], tc, hfl)
    assert not echo_top.isnull().all()

    fx_ds = fieldextra("intpl_k2any")

    # compare numerical results
    assert_allclose(
        fx_ds["ECHOTOPinM"].isel(z_1=0), echo_top.sel(z=15.0), rtol=1e-4, atol=1e-4
    )
    assert_allclose(
        fx_ds["ECHOTOP10inM"].isel(z_2=0), echo_top.sel(z=10.0), rtol=1e-4, atol=1e-4
    )
