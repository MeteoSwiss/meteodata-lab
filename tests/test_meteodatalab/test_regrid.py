# Standard library
import dataclasses as dc

# Third-party
import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_less

# First-party
from meteodatalab import data_source, grib_decoder
from meteodatalab.operators import regrid
from meteodatalab.operators.hzerocl import fhzerocl


@pytest.mark.data("original")
def test_regrid(data_dir, fieldextra):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    reader = grib_decoder.GribReader.from_files([cdatafile, datafile])
    ds = reader.load_fieldnames(["T", "HHL"])

    hzerocl = fhzerocl(ds["T"], ds["HHL"], extrapolate=True)
    out_regrid_target = "swiss,549500,149500,650500,250500,1000,1000"
    dst = regrid.RegularGrid.parse_regrid_operator(out_regrid_target)
    hzerocl.attrs["geography"] = ds["HHL"].geography
    observed = regrid.regrid(hzerocl, dst, regrid.Resampling.bilinear)

    fx_ds = fieldextra("regrid", out_regrid_target=out_regrid_target)
    expected = fx_ds["HZEROCL"]

    # The regrid operator is evaluated indirectly by comparing the output
    # to the one that is generated by fieldextra. Therefore, the reprojection errors
    # will manifest factored by the horizontal gradient of the supporting field.
    assert_allclose(observed, expected, rtol=5e-4)


def assert_close_enough(src, dst, rel):
    for field in dc.fields(src):
        if field.type == float:
            assert getattr(src, field.name) == pytest.approx(
                getattr(dst, field.name), rel=rel
            )
        else:
            assert getattr(src, field.name) == getattr(dst, field.name)


def test_to_crs():
    # 100km x 100km around Bern, LV03 -> LV 95
    nx, ny = 1001, 1000
    xmin, xmax = 550_000, 650_000
    ymin, ymax = 150_000, 250_000
    xoff = 2_000_000
    yoff = 1_000_000
    src = regrid.RegularGrid("epsg:21781", nx, ny, xmin, xmax, ymin, ymax)
    expected = regrid.RegularGrid(
        "epsg:2056", nx, ny, xmin + xoff, xmax + xoff, ymin + yoff, ymax + yoff
    )

    observed = src.to_crs("epsg:2056", dst_width=src.nx, dst_height=src.ny)

    # There's a bit less than half a pixel error...
    assert_close_enough(observed, expected, rel=1e-3)


@pytest.mark.data("iconremap")
@pytest.mark.parametrize("model_name", ["icon-ch1-eps", "icon-ch2-eps"])
def test_icon2geolatlon(data_dir, fieldextra, model_name):
    datafiles = [str(data_dir / f"{model_name.upper()}_lfff00000000_000")]
    source = data_source.FileDataSource(datafiles=datafiles)
    ds = grib_decoder.load(source, "T")
    original = ds["T"].attrs.copy()

    observed = regrid.icon2geolatlon(ds["T"])

    assert ds["T"].attrs == original

    out_regrid_target = {
        "icon-ch1-eps": "geolatlon,5500000,43600000,16900000,50000000,10000,10000",
        "icon-ch2-eps": "geolatlon,5500000,43600000,16900000,50000000,20000,20000",
    }
    root = "/oprusers/osm/opr.emme/data/ICON_INPUT"
    icon_grid_description = {
        "icon-ch1-eps": f"{root}/ICON-CH1-EPS/icon_grid_0001_R19B08_mch.nc",
        "icon-ch2-eps": f"{root}/ICON-CH2-EPS/icon_grid_0002_R19B07_mch.nc",
    }

    fx_ds = fieldextra(
        "iconremap",
        model_name=model_name,
        out_regrid_target=out_regrid_target[model_name],
        out_regrid_method="icontools,rbf",
        icon_grid_description=icon_grid_description[model_name],
        conf_files={
            "inputi": data_dir / f"{model_name.upper()}_lfff<DDHH>0000_000",
            "output": "<HH>_outfile.nc",
        },
    )

    mask = ~observed.isnull().values
    assert_allclose(observed, fx_ds["T"].where(mask), rtol=1e-4, atol=1e-4)


@pytest.mark.data("iconremap")
@pytest.mark.parametrize("model_name", ["icon-ch1-eps", "icon-ch2-eps"])
def test_icon2rotlatlon(data_dir, fieldextra, model_name):
    datafiles = [str(data_dir / f"{model_name.upper()}_lfff00000000_000")]
    source = data_source.FileDataSource(datafiles=datafiles)
    ds = grib_decoder.load(source, "T")

    observed = regrid.icon2rotlatlon(ds["T"])

    out_regrid_target = {
        "icon-ch1-eps": "rotlatlon,353140000,-4460000,4830000,3390000,10000,10000,"
        "190000000,43000000",
        "icon-ch2-eps": "rotlatlon,353180000,-4420000,4800000,3360000,20000,20000,"
        "190000000,43000000",
    }
    root = "/oprusers/osm/opr.emme/data/ICON_INPUT"
    icon_grid_description = {
        "icon-ch1-eps": f"{root}/ICON-CH1-EPS/icon_grid_0001_R19B08_mch.nc",
        "icon-ch2-eps": f"{root}/ICON-CH2-EPS/icon_grid_0002_R19B07_mch.nc",
    }

    fx_ds = fieldextra(
        "iconremap",
        model_name=model_name,
        out_regrid_target=out_regrid_target[model_name],
        out_regrid_method="icontools,rbf",
        icon_grid_description=icon_grid_description[model_name],
        conf_files={
            "inputi": data_dir / f"{model_name.upper()}_lfff<DDHH>0000_000",
            "output": "<HH>_outfile.nc",
        },
    )

    assert_allclose(observed, fx_ds["T"], rtol=1e-4, atol=1e-4)


@pytest.mark.data("iconremap")
@pytest.mark.parametrize("model_name", ["icon-ch1-eps", "icon-ch2-eps"])
def test_icon2swiss_small(data_dir, fieldextra, model_name):
    datafiles = [str(data_dir / f"{model_name.upper()}_lfff00000000_000")]
    source = data_source.FileDataSource(datafiles=datafiles)
    ds = grib_decoder.load(source, "T")

    # Use a small area centered around Bern
    regrid_target = "swiss,590000,190000,610000,210000,1000,1000"
    dst = regrid.RegularGrid.parse_regrid_operator(regrid_target)
    observed = regrid.iconremap(ds["T"], dst)

    # Sanity check the temperature values.
    extreme_low = np.full(observed.shape, 150)
    extreme_high = np.full(observed.shape, 350)
    assert_array_less(extreme_low, observed.values)
    assert_array_less(observed.values, extreme_high)

    # Verify that geolatlon coordinates are set and centered correctly.
    assert observed.lat.shape == (21, 21)
    assert observed.lon.shape == (21, 21)
    assert observed.lon[10][10] == pytest.approx(7.4386325, 1e-4)
    assert observed.lat[10][10] == pytest.approx(46.9510828, 1e-4)


@pytest.mark.skip(reason="the byc method in fx is not optimised (>30min on icon-ch1)")
@pytest.mark.data("iconremap")
@pytest.mark.parametrize("model_name", ["icon-ch1-eps", "icon-ch2-eps"])
def test_icon2swiss(data_dir, fieldextra, model_name):
    datafiles = [str(data_dir / f"{model_name.upper()}_lfff00000000_000")]
    source = data_source.FileDataSource(datafiles=datafiles)
    ds = grib_decoder.load(source, "T")

    out_regrid_target = {
        "icon-ch1-eps": "swiss,255500,-159500,964500,479500,1000,1000",
        "icon-ch2-eps": "swiss95,2439000,1040500,2867000,1334500,2000,2000",
    }

    dst = regrid.RegularGrid.parse_regrid_operator(out_regrid_target[model_name])
    observed = regrid.iconremap(ds["T"], dst)

    root = "/oprusers/osm/opr.emme/data/ICON_INPUT"
    icon_grid_description = {
        "icon-ch1-eps": f"{root}/ICON-CH1-EPS/icon_grid_0001_R19B08_mch.nc",
        "icon-ch2-eps": f"{root}/ICON-CH2-EPS/icon_grid_0002_R19B07_mch.nc",
    }

    fx_ds = fieldextra(
        "iconremap",
        model_name=model_name,
        out_regrid_target=out_regrid_target[model_name],
        out_regrid_method="icontools,byc",
        icon_grid_description=icon_grid_description[model_name],
        conf_files={
            "inputi": data_dir / f"{model_name.upper()}_lfff<DDHH>0000_000",
            "output": "<HH>_outfile.nc",
        },
    )

    assert_allclose(observed, fx_ds["T"], rtol=1e-2, atol=1)
