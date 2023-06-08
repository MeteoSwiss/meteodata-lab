# Third-party
from numpy.testing import assert_allclose

# First-party
import idpi.products.ninjo_k2th as ninjo
from idpi import grib_decoder


def test_product2(data_dir, fieldextra, grib_defs):
    datafile = data_dir / "lfff00000000.ch"
    cdatafile = data_dir / "lfff00000000c.ch"

    ds = {}
    grib_decoder.load_data(
        ds, ["U", "V", "W", "P", "T", "QV", "QC", "QI"], datafile, chunk_size=None
    )
    grib_decoder.load_data(ds, ["HHL", "HSURF"], cdatafile, chunk_size=None)

    observed_mean, observed_at_theta = ninjo.ninjo_k2th(
        ds["U"],
        ds["V"],
        ds["W"],
        ds["T"],
        ds["P"],
        ds["QV"],
        ds["QC"],
        ds["QI"],
        ds["HHL"],
    )

    fs_ds = fieldextra("ninjo_k2th")
    expected = fs_ds.rename({"x_1": "x", "y_1": "y", "z_2": "theta"})

    assert_allclose(
        observed_mean,
        expected["POT_VORTIC_MEAN"].squeeze(drop=True),
        atol=1e-6,
    )

    assert_allclose(
        observed_at_theta["pot_vortic"],
        expected["POT_VORTIC_AT_THETA"].squeeze(drop=True),
        atol=1e-9,
        rtol=1e-5,
    )

    assert_allclose(
        observed_at_theta["p"],
        expected["P"].squeeze(drop=True),
        atol=1e-3,
        rtol=1e-4,
    )

    assert_allclose(
        observed_at_theta["u"],
        expected["U"].squeeze(drop=True),
        atol=1e-9,
        rtol=1e-5,
    )

    assert_allclose(
        observed_at_theta["v"],
        expected["V"].squeeze(drop=True),
        atol=5e-4,
        rtol=1e-4,
    )
