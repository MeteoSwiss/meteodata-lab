# Standard library
import datetime as dt
import hashlib
import typing
from contextlib import nullcontext
from pathlib import Path
from unittest import mock

# Third-party
import pydantic
import pytest
import requests
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


def test_request_alias():
    req = ogd_api.Request(
        collection="ogd-forecasting-icon-ch1",
        variable="T",
        ref_time="2025-04-08T08:00:00Z",
        perturbed=False,
        lead_time="P0DT1H",
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


@pytest.mark.parametrize(
    "with_headers,valid_content,exc",
    [(True, True, None), (True, False, RuntimeError), (False, True, None)],
)
@mock.patch.object(ogd_api, "session", autospec=True)
def test_download_from_ogd(
    mock_session: mock.MagicMock,
    tmp_path: Path,
    with_headers: bool,
    valid_content: bool,
    exc: typing.Type[Exception] | None,
):
    content_main = b"main content"
    content_horizontal = b"horizontal content"
    content_vertical = b"vertical content"

    hash_main = hashlib.sha256(content_main).hexdigest()
    hash_horizontal = hashlib.sha256(content_horizontal).hexdigest()
    hash_vertical = hashlib.sha256(content_vertical).hexdigest()

    main_href = "https://test.com/path/to/some-file.grib"
    horizontal_href = "https://test.com/path/to/horizontal.grib"
    vertical_href = "https://test.com/path/to/vertical.grib"

    collections_url = "https://data.geo.admin.ch/api/stac/v1/collections"
    collection_id = "ch.meteoschweiz.ogd-forecasting-icon-ch2"
    assets_url = f"{collections_url}/{collection_id}/assets"

    mock_post_response = mock.Mock()
    mock_post_response.json.return_value = {
        "features": [{"assets": {"some-asset.ext": {"href": main_href}}}],
        "links": [],
    }

    if with_headers:
        headers_main = {"X-Amz-Meta-Sha256": hash_main}
        headers_horizontal = {"X-Amz-Meta-Sha256": hash_horizontal}
        headers_vertical = {"X-Amz-Meta-Sha256": hash_vertical}
    else:
        headers_main = {}
        headers_horizontal = {}
        headers_vertical = {}

    def mock_get_response(url, *args, **kwargs):
        # Respond with asset list for coordinate URLs
        if url == assets_url:
            assets = [
                {
                    "id": "horizontal_constants_icon-ch2-eps.grib2",
                    "href": horizontal_href,
                },
                {
                    "id": "vertical_constants_icon-ch2-eps.grib2",
                    "href": vertical_href,
                },
            ]
            return mock.Mock(
                spec=requests.Response,
                json=mock.Mock(return_value={"assets": assets}),
            )
        if url == main_href:
            content = content_main if valid_content else b"random content"
            return mock.Mock(
                spec=requests.Response,
                iter_content=mock.Mock(return_value=[content]),
                headers=headers_main,
            )
        if url == horizontal_href:
            return mock.Mock(
                spec=requests.Response,
                iter_content=mock.Mock(return_value=[content_horizontal]),
                headers=headers_horizontal,
            )
        if url == vertical_href:
            return mock.Mock(
                spec=requests.Response,
                iter_content=mock.Mock(return_value=[content_vertical]),
                headers=headers_vertical,
            )

        raise ValueError(f"Unexpected URL: {url}")

    mock_session.configure_mock(
        **{
            "post.return_value": mock_post_response,
            "get.side_effect": mock_get_response,
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
    cm = pytest.raises(exc) if exc is not None else nullcontext()

    with cm:
        ogd_api.download_from_ogd(req, target)

    if exc is not None:
        return

    assert (target / "some-file.grib").read_bytes() == content_main
    assert (target / "horizontal.grib").read_bytes() == content_horizontal
    assert (target / "vertical.grib").read_bytes() == content_vertical

    if with_headers:
        assert (target / "some-file.sha256").read_text() == hash_main
        assert (target / "horizontal.sha256").read_text() == hash_horizontal
        assert (target / "vertical.sha256").read_text() == hash_vertical
    else:
        assert not (target / "some-file.sha256").exists()
        assert not (target / "horizontal.sha256").exists()
        assert not (target / "vertical.sha256").exists()


@mock.patch.object(ogd_api, "_search")
def test_get_asset_urls_latest(mock_search: mock.MagicMock):
    mock_search.return_value = [
        "https://test.com/icon-ch1-eps-202505100000-1-v_10m-perturb.grib2",
        "https://test.com/icon-ch1-eps-202505120600-1-v_10m-perturb.grib2",
        "https://test.com/icon-ch1-eps-202505120000-1-v_10m-perturb.grib2",
        "https://test.com/icon-ch1-eps-202505110000-1-v_10m-perturb.grib2",
    ]

    req = ogd_api.Request(
        collection="ogd-forecasting-icon-ch1",
        variable="v_10m",
        reference_datetime="latest",
        perturbed=True,
        horizon="P0DT1H",
    )

    result = ogd_api.get_asset_urls(req)

    assert result == [
        "https://test.com/icon-ch1-eps-202505120600-1-v_10m-perturb.grib2"
    ]


@mock.patch.object(ogd_api, "_search")
def test_get_asset_urls_multiple_lead_times(mock_search: mock.MagicMock):
    mock_search.return_value = [
        "https://test.com/icon-ch1-eps-202505100000-1-v_10m-perturb.grib2",
        "https://test.com/icon-ch1-eps-202505100000-2-v_10m-perturb.grib2",
        "https://test.com/icon-ch1-eps-202505100000-3-v_10m-perturb.grib2",
        "https://test.com/icon-ch1-eps-202505110000-1-v_10m-perturb.grib2",
    ]

    req = ogd_api.Request(
        collection="ogd-forecasting-icon-ch1",
        variable="v_10m",
        reference_datetime="2025-05-10T00:00:00Z/..",
        perturbed=True,
        horizon=["P0DT1H", "P0DT2H", "P0DT3H"],
    )

    result = ogd_api.get_asset_urls(req)

    assert result == [
        "https://test.com/icon-ch1-eps-202505100000-1-v_10m-perturb.grib2",
        "https://test.com/icon-ch1-eps-202505100000-2-v_10m-perturb.grib2",
        "https://test.com/icon-ch1-eps-202505100000-3-v_10m-perturb.grib2",
    ]
