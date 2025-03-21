# Third-party
import pytest
import xarray as xr

# First-party
from meteodatalab import data_source, grib_decoder


@pytest.mark.parametrize(
    "params,levtype", [(["P", "T", "HHL"], "ml"), (["U_10M", "V_10M"], "sfc")]
)
def test_load(params, levtype, request_template, setup_fdb):
    source = data_source.FDBDataSource()
    request = request_template | {"param": params, "levtype": levtype}
    ds = grib_decoder.load(source, request)
    assert ds.keys() == set(params)
    assert all(arr.size != 0 for arr in ds.values())
    assert all(name == arr.parameter["shortName"] for name, arr in ds.items())


@pytest.mark.data("iconremap")
def test_load_icon_grid_balfrin_fallback(data_dir):
    datafiles = [str(data_dir / "ICON-CH1-EPS_lfff00000000_000")]
    source = data_source.FileDataSource(datafiles=datafiles)
    ds = grib_decoder.load(source, "T")
    assert ds.keys() == set(["T"])
    assert "lon" in ds["T"].coords
    assert "lat" in ds["T"].coords


def test_save(data_dir, tmp_path):
    datafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    reader = grib_decoder.GribReader.from_files([datafile])
    ds = reader.load_fieldnames(["HHL"])

    outfile = tmp_path / "output.grib"
    with outfile.open("wb") as f:
        grib_decoder.save(ds["HHL"], f, bits_per_value=24)

    reader = grib_decoder.GribReader.from_files([outfile])
    ds_new = reader.load_fieldnames(["HHL"])

    ds["HHL"].attrs.pop("metadata")
    ds_new["HHL"].attrs.pop("metadata")

    xr.testing.assert_identical(ds["HHL"], ds_new["HHL"])


@pytest.mark.parametrize("param", ("U", "V", "T"))
def test_save_field(data_dir, tmp_path, param):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00010000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    reader = grib_decoder.GribReader.from_files([datafile, cdatafile])
    ds = reader.load_fieldnames([param])

    outfile = tmp_path / "output.grib"
    with outfile.open("wb") as f:
        grib_decoder.save(ds[param], f)

    reader = grib_decoder.GribReader.from_files([outfile, cdatafile])
    ds_new = reader.load_fieldnames([param])

    ds[param].attrs.pop("metadata")
    ds_new[param].attrs.pop("metadata")

    xr.testing.assert_identical(ds[param], ds_new[param])
