# Third-party
import pytest
import xarray as xr

# First-party
from idpi import grib_decoder


def test_save(data_dir, tmp_path):
    datafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    reader = grib_decoder.GribReader.from_files([datafile])
    ds = reader.load_fieldnames(["HHL"])

    outfile = tmp_path / "output.grib"
    with outfile.open("wb") as f:
        grib_decoder.save(ds["HHL"], f, bits_per_value=24)

    reader = grib_decoder.GribReader.from_files([outfile])
    ds_new = reader.load_fieldnames(["HHL"])

    ds["HHL"].attrs.pop("message")
    ds_new["HHL"].attrs.pop("message")

    xr.testing.assert_identical(ds["HHL"], ds_new["HHL"])


@pytest.mark.parametrize("param", ("U", "V", "T"))
def test_save_field(data_dir, tmp_path, param):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    reader = grib_decoder.GribReader.from_files([datafile, cdatafile])
    ds = reader.load_fieldnames([param])

    outfile = tmp_path / "output.grib"
    with outfile.open("wb") as f:
        grib_decoder.save(ds[param], f)

    reader = grib_decoder.GribReader.from_files([outfile, cdatafile])
    ds_new = reader.load_fieldnames([param])

    ds[param].attrs.pop("message")
    ds_new[param].attrs.pop("message")

    xr.testing.assert_identical(ds[param], ds_new[param])
