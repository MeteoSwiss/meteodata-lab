# Third-party
import pytest

# First-party
from idpi import mars


@pytest.fixture
def sample():
    # for param=U, date=20200101, time=0000
    return {
        "class": "od",
        "date": "20200101",
        "expver": "0001",
        "levtype": "ml",
        "levelist": list(range(1, 81)),
        "model": "COSMO-1E",
        "number": 0,
        "stream": "enfo",
        "param": 500028,  # U
        "time": "0000",
        "type": "ememb",
        "step": 0,
    }


def test_fdb_defaults(sample):
    observed = mars.Request("U", date="20200101", time="0000").to_fdb()
    expected = sample

    assert observed == expected


def test_fdb_c2e(sample):
    observed = mars.Request(
        "U",
        date="20200101",
        time="0000",
        model=mars.Model.COSMO_2E,
    ).to_fdb()
    expected = sample | {"model": "COSMO-2E", "levelist": list(range(1, 61))}

    assert observed == expected


def test_fdb_sfc(sample):
    observed = mars.Request(
        "HSURF",
        date="20200101",
        time="0000",
        levtype=mars.LevType.SURFACE,
    ).to_fdb()
    sample.pop("levelist")
    expected = sample | {"param": 500007, "levtype": "sfc"}

    assert observed == expected


def test_request_raises():
    with pytest.raises(ValueError):
        mars.Request("U", date="20200101", time="0000", model="undef")


def test_multiple_params(sample):
    observed = mars.Request(("U", "V"), date="20200101", time="0000").to_fdb()
    expected = sample | {"param": [500028, 500030]}

    assert observed == expected


def test_any_staggering(sample):
    observed = mars.Request(("U", "V", "W"), date="20200101", time="0000").to_fdb()
    expected = sample | {
        "param": [500028, 500030, 500032],
        "levelist": list(range(1, 82)),
    }

    assert observed == expected


def test_feature_timeseries(sample):
    feature = mars.TimeseriesFeature(
        points=[mars.Point(0.1, 0.2)],
        start=0,
        end=300,
    )
    observed = mars.Request("U", date="20200101", time="0000", feature=feature).to_fdb()
    expected = sample | {
        "feature": {
            "type": "timeseries",
            "points": [[0.1, 0.2]],
            "start": 0,
            "end": 300,
        }
    }

    assert observed == expected
