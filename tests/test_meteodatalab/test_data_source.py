# Standard library
import http.server
import threading
from contextlib import nullcontext
from unittest.mock import call, patch

# Third-party
import pytest

# First-party
from meteodatalab import config, data_source, mars


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

    source = data_source.FileDataSource(datafiles=datafiles)
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

    source = data_source.FileDataSource(datafiles=datafiles)
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
        source = data_source.FileDataSource(datafiles=datafiles)
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

    source = data_source.FDBDataSource(request_template=template)
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

    source = data_source.FDBDataSource(request_template=template)
    for _ in source.retrieve(request):
        pass

    assert mock_grib_def_ctx.mock_calls == [call("cosmo")]
    assert mock_from_source.mock_calls == [
        call("fdb", mars.Request(param, **template).to_fdb()),
        call().__iter__(),
    ]


PORT = 8787


@pytest.fixture
def server(data_dir):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(data_dir), **kwargs)

    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever)
        thread.daemon = True
        thread.start()
        yield
        httpd.shutdown()


def test_retrieve_url(server):
    urls = [f"http://localhost:{PORT}/COSMO-1E/1h/ml_sl/000/lfff00000000"]
    source = data_source.URLDataSource(urls=urls)
    for field in source.retrieve({"param": "T"}):
        assert field.metadata("shortName") == "T"


# TODO: which one to use?
def test_retrieve_stream_mock(mock_from_source, mock_grib_def_ctx):
    streamfile = "foo"
    param = "bar"

    with open(streamfile, "w") as f:
        source = data_source.StreamDataSource(stream=f)
        for _ in source.retrieve(param):
            pass

    assert mock_grib_def_ctx.mock_calls == [call("cosmo")]
    assert mock_from_source.mock_calls == [
        call("stream", f),
        call().__iter__(),
    ]


def test_retrieve_stream(data_dir):
    datafile = data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000"
    request = {"param": "T", "levelist": 10}

    with open(datafile, "rb") as f:
        source = data_source.StreamDataSource(stream=f)
        for field in source.retrieve(request):
            assert field.metadata("shortName") == "T"
            assert field.metadata("levelist") == 10
