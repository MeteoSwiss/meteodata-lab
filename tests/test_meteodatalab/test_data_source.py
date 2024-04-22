# Standard library
from contextlib import nullcontext
from unittest.mock import call, patch

# Third-party
import pytest

# First-party
from idpi import config, data_source, mars


@pytest.fixture
def mock_from_source():
    with patch.object(data_source.ekd, "from_source") as mock:
        yield mock


@pytest.fixture
def mock_grib_def_ctx():
    with patch.object(data_source, "grib_def_ctx") as mock:
        mock.return_value = nullcontext()
        yield mock


def test_retrieve_files(mock_from_source, mock_grib_def_ctx):
    datafiles = ["foo"]
    param = "bar"

    source = data_source.DataSource(datafiles)
    for _ in source.retrieve(param):
        pass

    assert mock_grib_def_ctx.mock_calls == [call("cosmo")]
    assert mock_from_source.mock_calls == [
        call("file", datafiles),
        call().sel({"param": param}),
        call().sel().__iter__(),
    ]


def test_retrieve_files_tuple(mock_from_source, mock_grib_def_ctx):
    datafiles = ["foo"]
    request = param, levtype = ("bar", "ml")

    source = data_source.DataSource(datafiles)
    for _ in source.retrieve(request):
        pass

    assert mock_grib_def_ctx.mock_calls == [call("cosmo")]
    assert mock_from_source.mock_calls == [
        call("file", datafiles),
        call().sel({"param": param, "levtype": levtype}),
        call().sel().__iter__(),
    ]


def test_retrieve_files_ifs(mock_from_source, mock_grib_def_ctx):
    datafiles = ["foo"]
    param = "bar"

    with config.set_values(data_scope="ifs"):
        source = data_source.DataSource(datafiles)
        for _ in source.retrieve(param):
            pass

    assert mock_grib_def_ctx.mock_calls == [call("ifs")]
    assert mock_from_source.mock_calls == [
        call("file", datafiles),
        call().sel({"param": param}),
        call().sel().__iter__(),
    ]


def test_retrieve_fdb(mock_from_source, mock_grib_def_ctx):
    param = "U"
    template = {"date": "20200101", "time": "0000"}

    source = data_source.DataSource(request_template=template)
    for _ in source.retrieve(param):
        pass

    assert mock_grib_def_ctx.mock_calls == [call("cosmo")]
    assert mock_from_source.mock_calls == [
        call("fdb", mars.Request(param, **template).to_fdb()),
        call().__iter__(),
    ]


def test_retrieve_fdb_mars(mock_from_source, mock_grib_def_ctx):
    param = "U"
    request = mars.Request(param=param)
    template = {"date": "20200101", "time": "0000"}

    source = data_source.DataSource(request_template=template)
    for _ in source.retrieve(request):
        pass

    assert mock_grib_def_ctx.mock_calls == [call("cosmo")]
    assert mock_from_source.mock_calls == [
        call("fdb", mars.Request(param, **template).to_fdb()),
        call().__iter__(),
    ]
