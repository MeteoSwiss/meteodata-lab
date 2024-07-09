# Third-party
from numpy.testing import assert_allclose

# First-party
from meteodatalab.grib_decoder import GribReader
from meteodatalab.operators.destagger import destagger
from meteodatalab.operators.vertical_interpolation import (
    TargetCoordinates,
    TargetCoordinatesAttrs,
    interpolate_k2any,
)


def test_intpl_k2theta(data_dir, fieldextra):
    # define target coordinates
    tc = TargetCoordinates(
        type_of_level="echoTopInM",
        values=[15.0],
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
    reader = GribReader.from_files([cdatafile, datafile])
    ds = reader.load_fieldnames(["DBZ", "HHL"])

    hfl = destagger(ds["HHL"].squeeze(drop=True), "z")

    # call interpolation operator
    echo_top = interpolate_k2any(hfl, "high_fold", ds["DBZ"], tc, hfl)

    fx_ds = fieldextra("intpl_k2any")

    # compare numerical results
    assert_allclose(fx_ds["ECHOTOPinM"], echo_top, rtol=1e-4, atol=1e-4)
