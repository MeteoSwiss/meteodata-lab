"""Data source helper class."""

# Standard library
import dataclasses as dc
import sys
import typing
import os
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager, nullcontext
from functools import singledispatchmethod
from pathlib import Path

# Third-party
import earthkit.data as ekd  # type: ignore
import eccodes  # type: ignore
import polytope  # type: ignore

# Local
from . import config, mars


@contextmanager
def cosmo_grib_defs():
    """Enable COSMO GRIB definitions."""
    if "ECCODES_DEFINITION_PATH" in os.environ or "GRIB_DEFINITION_PATH" in os.environ:
        return nullcontext()

    restore = eccodes.codes_definition_path()
    root_dir = Path(sys.prefix) / "share"
    paths = (
        root_dir / "eccodes-cosmo-resources/definitions",
        Path(restore),
    )
    for path in paths:
        if not path.exists():
            raise RuntimeError(f"{path} does not exist")
    defs_path = ":".join(map(str, paths))
    eccodes.codes_set_definitions_path(defs_path)
    try:
        yield
    finally:
        eccodes.codes_set_definitions_path(restore)


def grib_def_ctx(grib_def: str):
    if grib_def == "cosmo":
        return cosmo_grib_defs()
    return nullcontext()


@dc.dataclass
class DataSource(ABC):
    request_template: dict[str, typing.Any] = dc.field(default_factory=dict)

    @singledispatchmethod
    def retrieve(
        self, request: dict[str, typing.Any] | str | tuple[str, str] | mars.Request
    ) -> Iterator:
        """Stream GRIB fields from files or FDB.

        Request for data from the source in the mars language.

        Simple strings are interpreted as `param` filters and pairs of strings
        are interpreted as `param` and `levtype` filters.

        Key value pairs from the `request_template` attribute are used as default
        values. Note that the default values in the mars request passed as an input
        will take precedence on the template values.

        Parameters
        ----------
        request : dict | str | tuple[str, str] | meteodatalab.mars.Request
            Request for data from the source in the mars language.

        Yields
        ------
        GribField
            GribField instances containing the requested data.

        """
        raise NotImplementedError(f"request of type {type(request)} not supported.")

    @retrieve.register
    def _(self, request: dict) -> Iterator:
        # The presence of the yield keyword makes this def a generator.
        # As a result, the context manager will remain active until the
        # exhaustion of the data source iterator.
        grib_def = config.get("data_scope", "cosmo")
        with grib_def_ctx(grib_def):
            yield from self._retrieve(request)

    @retrieve.register
    def _(self, request: mars.Request) -> Iterator:
        yield from self.retrieve(request.dump())

    @retrieve.register
    def _(self, request: str) -> Iterator:
        yield from self.retrieve({"param": request})

    @retrieve.register
    def _(self, request: tuple) -> Iterator:
        param, levtype = request
        yield from self.retrieve({"param": param, "levtype": levtype})

    @abstractmethod
    def _retrieve(self, request: dict):
        pass


@dc.dataclass
class FDBDataSource(DataSource):
    def _retrieve(self, request: dict):
        req_kwargs = self.request_template | request
        req = mars.Request(**req_kwargs)
        yield from ekd.from_source("fdb", req.to_fdb())


@dc.dataclass
class FileDataSource(DataSource):
    datafiles: list[str] | None = None

    def _retrieve(self, request: dict):
        req_kwargs = self.request_template | request
        _ = mars.Request(**req_kwargs)
        fs = ekd.from_source("file", self.datafiles)
        yield from fs.sel(req_kwargs)


@dc.dataclass
class PolytopeDataSource(DataSource):
    polytope_collection: str | None = None
    polytope_client: polytope.api.Client = dc.field(init=False)

    def __post_init__(self):
        self.polytope_client = polytope.api.Client()

    def _retrieve(self, request: dict):
        req_kwargs = self.request_template | request
        req = mars.Request(**req_kwargs)
        pointers = self.polytope_client.retrieve(
            self.polytope_collection,
            req.to_polytope(),
            pointer=True,
            asynchronous=False,
        )
        urls = [p["location"] for p in pointers]
        yield from ekd.from_source("url", urls, stream=True)


@dc.dataclass
class URLDataSource(DataSource):
    urls: list[str] | None = None

    def _retrieve(self, request: dict):
        req_kwargs = self.request_template | request
        fs = ekd.from_source("url", self.urls)
        yield from fs.sel(**req_kwargs)
