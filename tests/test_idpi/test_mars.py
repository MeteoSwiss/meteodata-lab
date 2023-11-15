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
        "number": 1,
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


def test_no_defaults():
    observed = mars.Request("U").dump(exclude_defaults=True)
    expected = {"param": "U"}

    assert observed == expected
