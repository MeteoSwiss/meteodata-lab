# Third-party
import pytest

# First-party
from meteodatalab.grib_decoder import load
from meteodatalab.data_source import FileDataSource
from meteodatalab.metadata import set_origin_xy, is_staggered
from meteodatalab.operators.destagger import destagger


def test_staggered_cosmo_data(data_dir):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    source = FileDataSource(datafiles=[cdatafile, datafile])
    ds = load(source, {"param": ["U", "V", "HHL", "T"]})
    
    with pytest.raises(ValueError, match="run set_origin_xy"):
        is_staggered(ds["U"])

    set_origin_xy(ds, ref_param="HHL")

    assert is_staggered(ds["U"])
    assert is_staggered(ds["V"])
    assert not is_staggered(ds["HHL"])
    assert not is_staggered(ds["T"])


@pytest.mark.data("iconremap")
def test_icon_data_not_staggered(data_dir, geo_coords):
    datafiles = [str(data_dir / "ICON-CH1-EPS_lfff00000000_000")]
    source = FileDataSource(datafiles=datafiles)
    ds = load(source, {"param": ["U", "V", "T"]}, geo_coords=geo_coords)

    assert not is_staggered(ds["U"])
    assert not is_staggered(ds["V"])
    assert not is_staggered(ds["T"])