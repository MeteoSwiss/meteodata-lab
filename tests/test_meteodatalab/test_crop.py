# Third-party
from numpy.testing import assert_equal

# First-party
from idpi.grib_decoder import GribReader
from idpi.operators import crop, gis


def test_crop(data_dir):
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    reader = GribReader.from_files([cdatafile])
    ds = reader.load_fieldnames(["HHL"])
    hhl = ds["HHL"]

    observed = crop.crop(hhl, crop.Bounds(1, 2, 3, 5))

    grid = gis.get_grid(hhl.geography)
    cropped = hhl.assign_coords(x=grid.rlon, y=grid.rlat).isel(x=[1, 2], y=[3, 4, 5])

    expected_values = cropped.values
    expected_geography = hhl.geography | {
        "Ni": 2,
        "Nj": 3,
        "longitudeOfFirstGridPointInDegrees": cropped.coords["x"].min().item(),
        "longitudeOfLastGridPointInDegrees": cropped.coords["x"].max().item(),
        "latitudeOfFirstGridPointInDegrees": cropped.coords["y"].min().item(),
        "latitudeOfLastGridPointInDegrees": cropped.coords["y"].max().item(),
    }

    assert_equal(observed.values, expected_values)
    assert observed.geography == expected_geography
    assert observed.parameter == hhl.parameter
