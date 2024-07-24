# Third-party
import pytest

# First-party
from meteodatalab import data_source, grib_decoder, metadata


@pytest.mark.parametrize(
    "keys,values",
    [
        ("shortName", "HHL"),
        (["number", "step"], [0, 0]),
        (("typeOfLevel"), ("generalVertical")),
    ],
)
def test_extract_keys(data_dir, keys, values):
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    source = data_source.DataSource([str(cdatafile)])
    ds = grib_decoder.load(source, {"param": ["HHL"]})

    observed = metadata.extract_keys(ds["HHL"].message, keys)
    expected = values

    assert observed == expected


def test_extract_keys_raises(data_dir):
    cdatafile = data_dir / "COSMO-1E/1h/const/000/lfff00000000c"

    source = data_source.DataSource([str(cdatafile)])
    ds = grib_decoder.load(source, {"param": ["HHL"]})

    with pytest.raises(ValueError):
        metadata.extract_keys(ds["HHL"].message, None)
