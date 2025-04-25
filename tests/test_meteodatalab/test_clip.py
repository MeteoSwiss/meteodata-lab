# Third-party
import pytest
import xarray as xr

# First-party
from meteodatalab import data_source, grib_decoder
from meteodatalab.operators import clip


@pytest.mark.data("iconremap")
def test_clip_lateral_boundary_strip(data_dir):
    datafile = str(data_dir / "ICON-CH1-EPS_lfff00000000_000")

    reader = data_source.FileDataSource(datafiles=[datafile])
    ds = grib_decoder.load(reader, {"param": ["T_2M"]})
    ori = ds["T_2M"]
    ori_uuid = ori.metadata.get("uuidOfHGrid")

    res_14 = clip.clip_lateral_boundary_strip(ori, 14)
    res_7 = clip.clip_lateral_boundary_strip(ori, 7)

    # check that the size of the clipped data is actually smaller
    assert res_14.size < res_7.size < ori.size

    # check that the new UUID differs from the original depending on the parameter
    res_14_uuid = res_14.metadata.get("uuidOfHGrid")
    res_7_uuid = res_7.metadata.get("uuidOfHGrid")
    assert res_14_uuid != ori_uuid
    assert res_7_uuid != ori_uuid
    assert res_14_uuid != res_7_uuid

    # check that the new UUID is the same for same parameter
    res_14_clone = clip.clip_lateral_boundary_strip(ori, 14)
    assert res_14_uuid == res_14_clone.metadata.get("uuidOfHGrid")


@pytest.mark.data("iconremap")
def test_clip_lateral_boundary_strip_gridfile(data_dir, tmp_path):
    datafile = str(data_dir / "ICON-CH1-EPS_lfff00000000_000")

    reader = data_source.FileDataSource(datafiles=[datafile])
    ds = grib_decoder.load(reader, {"param": ["T_2M"]})
    ori = ds["T_2M"]

    # perform clipping and save the new grid descriptor file
    res = clip.clip_lateral_boundary_strip(
        ori, 14, new_gridfile=tmp_path / "_test_gridfile.nc"
    )

    # save the clipped data to a GRIB file
    outfile = tmp_path / "_test_clip.grib"
    with outfile.open("wb") as f:
        grib_decoder.save(res, f)

    # read the clipped data back, using the new grid descriptor file
    def _geo_coords_cbk(uuid=None):
        ds = xr.open_dataset(tmp_path / "_test_gridfile.nc")
        return {"lat": ds.clat, "lon": ds.clon}

    reader = data_source.FileDataSource(datafiles=[str(outfile)])
    ds = grib_decoder.load(reader, {"param": ["T_2M"]}, geo_coords=_geo_coords_cbk)
