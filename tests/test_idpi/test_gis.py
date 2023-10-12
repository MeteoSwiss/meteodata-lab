# Third-party
import numpy as np
import pytest
import xarray as xr
from numpy.testing import assert_allclose

# First-party
from idpi import grib_decoder
from idpi.operators import gis


@pytest.fixture
def coords():
    wgs84 = [
        (46.21985, 7.33775),
        (46.99753, 6.94804),
        (45.93692, 7.86675),
        (46.37458, 10.03132),
        (47.67706, 8.61496),
    ]
    swiss_lv03 = [
        (592215.36, 118716.55),
        (562685.81, 205279.87),
        (633205.62, 87350.03),
        (799451.68, 139208.03),
        (688334.86, 281376.61),
    ]
    return wgs84, swiss_lv03


def test_geolatlon2swiss(coords):
    wgs84, swiss_lv03 = coords
    expected = np.array(swiss_lv03).T

    lat, lon = zip(*wgs84)
    lat_xr = xr.DataArray(list(lat), dims="pt")
    lon_xr = xr.DataArray(list(lon), dims="pt")

    observed = gis.geolatlon2swiss(lon_xr, lat_xr)

    assert_allclose(observed, expected, atol=1.5)


def test_vref_rot2geolatlon(data_dir, fieldextra):
    datafile = data_dir / "lfff00000000.ch"

    reader = grib_decoder.GribReader([datafile], ref_param="T")
    ds = reader.load_fields(["U_10M", "V_10M"])

    u_g, v_g = gis.vref_rot2geolatlon(ds["U_10M"], ds["V_10M"])

    fx_ds = fieldextra("n2geog")

    assert_allclose(u_g.isel(z=0), fx_ds["U_10M"], atol=1e-5, rtol=1e-6)
    assert_allclose(v_g.isel(z=0), fx_ds["V_10M"], atol=1e-5, rtol=1e-6)
