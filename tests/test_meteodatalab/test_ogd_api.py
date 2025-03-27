# Standard library
import datetime as dt
import hashlib
from contextlib import nullcontext
from pathlib import Path
from unittest import mock

# Third-party
import pydantic
import pytest
import xarray as xr

# First-party
from meteodatalab import ogd_api


def test_request_dump():
    req = ogd_api.Request(
        collection="ogd-forecasting-icon-ch1",
        variable="T",
        reference_datetime="2025-04-08T08:00:00Z",
        perturbed=False,
        horizon="P0DT1H",
    )
    observed = req.dump()
    expected = {
        "collections": ["ch.meteoschweiz.ogd-forecasting-icon-ch1"],
        "forecast:variable": "T",
        "forecast:reference_datetime": "2025-04-08T08:00:00Z",
        "forecast:perturbed": False,
        "forecast:horizon": "PT1H",
    }

    assert observed == expected


@pytest.mark.parametrize("key", ["collection", "reference_datetime", "horizon"])
def test_request_invalid(key):
    kwargs = dict(
        collection="ogd-forecasting-icon-ch1",
        variable="T",
        reference_datetime="2025-04-08T08:00:00Z",
        perturbed=False,
        horizon="P0DT1H",
    )
    kwargs[key] = "invalid"
    with pytest.raises(pydantic.ValidationError):
        ogd_api.Request(**kwargs)


@pytest.mark.parametrize(
    "value,valid",
    [
        ("2025-04-08T08:00:00Z", True),
        ("../2025-04-08T08:00:00Z", True),
        ("2025-04-08T08:00:00Z/..", True),
        ("2025-04-08T08:00:00Z/2025-04-09T08:00:00Z", True),
        (dt.datetime.now(dt.timezone.utc), True),
        ("not a date", False),
        (1744786857, False),
        ("2025-04-08T08:00:00Z/2025-04-07T08:00:00Z", False),
        ("2025-04-08T08:00:00Z/2025-04-09T08:00:00Z/2025-04-10T08:00:00Z", False),
    ],
)
def test_reference_datetime(value, valid):
    cm = nullcontext() if valid else pytest.raises(pydantic.ValidationError)
    with cm:
        observed = ogd_api.Request(
            collection="ogd-forecasting-icon-ch1",
            variable="T",
            reference_datetime=value,
            perturbed=False,
            horizon="P0DT1H",
        )

    if valid:
        expected = (
            value
            if not isinstance(value, dt.datetime)
            else value.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        assert observed.reference_datetime == expected


@mock.patch.object(ogd_api, "session", autospec=True)
def test_get_from_ogd(mock_session: mock.MagicMock, data_dir: Path):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    body = {
        "features": [{"assets": {"some-asset.ext": {"href": f"file://{datafile}"}}}],
        "links": [],
    }
    mock_response = mock.Mock(**{"json.return_value": body})
    mock_session.configure_mock(**{"post.return_value": mock_response})

    req = ogd_api.Request(
        collection="ogd-forecasting-icon-ch2",
        variable="T",
        reference_datetime="2025-04-08T08:00:00Z",
        perturbed=False,
        horizon="P0DT1H",
    )
    observed = ogd_api.get_from_ogd(req)

    assert isinstance(observed, xr.DataArray)
    assert observed.parameter["shortName"] == "T"


@pytest.mark.parametrize("with_headers", [True, False])
@mock.patch.object(ogd_api, "session", autospec=True)
def test_download_from_ogd(
    mock_session: mock.MagicMock, tmp_path: Path, with_headers: bool
):
    content = b"some content"
    href = "https://test.com/path/to/some-file.grib"
    body = {
        "features": [{"assets": {"some-asset.ext": {"href": href}}}],
        "links": [],
    }
    mock_post_response = mock.Mock(**{"json.return_value": body})
    if with_headers:
        headers = {"X-Amz-Meta-Sha256": hashlib.sha256(content).hexdigest()}
    else:
        headers = {}
    mock_get_response = mock.Mock(
        headers=headers, **{"iter_content.return_value": [content]}
    )
    mock_session.configure_mock(
        **{
            "post.return_value": mock_post_response,
            "get.return_value": mock_get_response,
        }
    )

    req = ogd_api.Request(
        collection="ogd-forecasting-icon-ch2",
        variable="T",
        reference_datetime="2025-04-08T08:00:00Z",
        perturbed=False,
        horizon="P0DT1H",
    )
    target = tmp_path / "out"
    target.mkdir()
    ogd_api.download_from_ogd(req, target)

    observed = (target / "some-file.grib").read_bytes()
    expected = content

    assert observed == expected
