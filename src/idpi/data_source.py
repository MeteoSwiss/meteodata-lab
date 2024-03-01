"""Data source helper class."""

# Standard library
import dataclasses as dc
import sys
import typing
from collections.abc import Iterator
from contextlib import contextmanager, nullcontext
from functools import singledispatchmethod
from pathlib import Path

# Third-party
import earthkit.data as ekd  # type: ignore
import eccodes  # type: ignore

# Local
from . import config, mars

GRIB_DEF = {
    mars.Model.COSMO_1E: "cosmo",
    mars.Model.COSMO_2E: "cosmo",
    mars.Model.ICON_CH1_EPS: "cosmo",
    mars.Model.ICON_CH2_EPS: "cosmo",
}


@contextmanager
def cosmo_grib_defs():
    """Enable COSMO GRIB definitions."""
    root_dir = Path(sys.prefix) / "share"
    paths = (
        root_dir / "eccodes-cosmo-resources/definitions",
        root_dir / "eccodes/definitions",
    )
    for path in paths:
        if not path.exists():
            raise RuntimeError(f"{path} does not exist")
    defs_path = ":".join(map(str, paths))
    restore = eccodes.codes_definition_path()
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
class DataSource:
    datafiles: list[str] | None = None
    request_template: dict[str, typing.Any] = dc.field(default_factory=dict)

    @singledispatchmethod
    def retrieve(
        self, request: dict[str, typing.Any] | str | tuple[str, str]
    ) -> Iterator:
        """Stream GRIB fields from files or FDB.

        Request for data from the source in the mars language.
        The data source is defined by the `datafiles` attribute if provided otherwise
        FDB is used.
        Simple strings are interpreted as `param` filters and pairs of strings
        are interpreted as `param` and `levtype` filters.
        Key value pairs from the `request_template` attribute are used as default
        values.

        Parameters
        ----------
        request : dict | str | tuple[str, str]
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
        req_kwargs = self.request_template | request
        # validate the request
        req = mars.Request(**req_kwargs)

        grib_def = config.get("data_scope", GRIB_DEF[req.model])
        with grib_def_ctx(grib_def):
            if self.datafiles:
                fs = ekd.from_source("file", self.datafiles)
                source = fs.sel(req_kwargs)
                # ideally, the sel would be done with the mars request but
                # fdb and file sources currently disagree on the type of the
                # date and time fields.
                # see: https://github.com/ecmwf/earthkit-data/issues/253
            else:
                source = ekd.from_source("fdb", req.to_fdb())
            yield from source  # type: ignore

    @retrieve.register
    def _(self, request: str) -> Iterator:
        yield from self.retrieve({"param": request})

    @retrieve.register
    def _(self, request: tuple) -> Iterator:
        param, levtype = request
        yield from self.retrieve({"param": param, "levtype": levtype})
