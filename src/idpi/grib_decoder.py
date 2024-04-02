"""Decoder for grib data."""

# Standard library
import dataclasses as dc
import datetime as dt
import io
import logging
import typing
from collections.abc import Mapping, Sequence
from itertools import product
from pathlib import Path
from warnings import warn

# Third-party
import earthkit.data as ekd  # type: ignore
import numpy as np
import xarray as xr
from numpy.typing import DTypeLike

# Local
from . import data_source, mars, metadata, tasking

logger = logging.getLogger(__name__)

DIM_MAP = {
    "level": "z",
    "perturbationNumber": "eps",
    "step": "time",
}
INV_DIM_MAP = {v: k for k, v in DIM_MAP.items()}

Request = str | tuple | dict | mars.Request


class GribField(typing.Protocol):
    def metadata(self, *args, **kwargs) -> typing.Any: ...
    def message(self) -> bytes: ...
    def to_numpy(self, dtype: DTypeLike) -> np.ndarray: ...
    def to_latlon(self) -> dict[str, np.ndarray]: ...


class MissingData(RuntimeError):
    pass


def _is_ensemble(field) -> bool:
    try:
        return field.metadata("typeOfEnsembleForecast") == 192
    except KeyError:
        return False


def _parse_datetime(date, time):
    return dt.datetime.strptime(f"{date}{time:04d}", "%Y%m%d%H%M")


def _extract_pv(pv):
    if pv is None:
        return {}
    i = len(pv) // 2
    return {
        "ak": xr.DataArray(pv[:i], dims="z"),
        "bk": xr.DataArray(pv[i:], dims="z"),
    }


@dc.dataclass
class _FieldBuffer:
    dims: tuple[str, ...] | None = None
    hcoords: dict[str, xr.DataArray] = dc.field(default_factory=dict)
    metadata: dict[str, typing.Any] = dc.field(default_factory=dict)
    time_meta: dict[int, dict] = dc.field(default_factory=dict)
    values: dict[tuple[int, ...], np.ndarray] = dc.field(default_factory=dict)

    def load(self, field: GribField) -> None:
        dim_keys = (
            ("perturbationNumber", "step", "level")
            if _is_ensemble(field)
            else ("step", "level")
        )
        key = field.metadata(*dim_keys)
        logger.debug("Received field for key: %s", key)
        self.values[key] = field.to_numpy(dtype=np.float32)

        step = key[-2]  # assume all members share the same time steps
        if step not in self.time_meta:
            self.time_meta[step] = field.metadata(namespace="time")

        if not self.dims:
            self.dims = tuple(DIM_MAP[d] for d in dim_keys) + ("y", "x")

        if not self.metadata:
            self.metadata = {
                "message": field.message(),
                **metadata.extract(field.metadata()),
            }

        if not self.hcoords:
            self.hcoords = {
                dim: xr.DataArray(dims=("y", "x"), data=values)
                for dim, values in field.to_latlon().items()
            }

    def _gather_coords(self):
        if self.dims is None:
            raise RuntimeError("No dims.")

        coord_values = zip(*self.values)
        unique = (sorted(set(values)) for values in coord_values)
        coords = {dim: c for dim, c in zip(self.dims[:-2], unique)}

        if missing := [
            combination
            for combination in product(*coords.values())
            if combination not in self.values
        ]:
            msg = f"Missing combinations: {missing}"
            logger.exception(msg)
            raise RuntimeError(msg)

        ny, nx = next(iter(self.values.values())).shape
        shape = tuple(len(v) for v in coords.values()) + (ny, nx)
        return coords, shape

    def _gather_tcoords(self):
        time = None
        valid_time = []
        for step in sorted(self.time_meta):
            tm = self.time_meta[step]
            valid_time.append(_parse_datetime(tm["validityDate"], tm["validityTime"]))
            if time is None:
                time = _parse_datetime(tm["dataDate"], tm["dataTime"])

        return {"valid_time": ("time", valid_time), "ref_time": time}

    def to_xarray(self) -> xr.DataArray:
        if not self.values:
            raise MissingData("No values.")

        coords, shape = self._gather_coords()
        tcoords = self._gather_tcoords()

        array = xr.DataArray(
            data=np.array(
                [self.values.pop(key) for key in sorted(self.values)]
            ).reshape(shape),
            coords=coords | self.hcoords | tcoords,
            dims=self.dims,
            attrs=self.metadata,
        )

        if array.vcoord_type != "surface":
            return array

        return array.squeeze("z", drop=True)


def _load_buffer_map(
    source: data_source.DataSource,
    request: Request,
) -> dict[str, _FieldBuffer]:
    logger.info("Retrieving request: %s", request)
    fs = source.retrieve(request)

    buffer_map: dict[str, _FieldBuffer] = {}

    for field in fs:
        name = field.metadata("shortName")
        buffer = buffer_map.setdefault(name, _FieldBuffer())
        buffer.load(field)

    return buffer_map


def load_single_param(
    source: data_source.DataSource,
    request: Request,
) -> xr.DataArray:
    """Request data from a data source for a single parameter.

    Parameters
    ----------
    source : data_source.DataSource
        Source to request the data from.
    request : str | tuple[str, str] | dict[str, Any]
        Request for data from the source in the mars language.

    Raises
    ------
    ValueError
        if more than one param is present in the request.
    RuntimeError
        when all of the requested data is not returned from the data source.

    Returns
    -------
    xarray.DataArray
        A data array of the requested field.

    """
    if (
        isinstance(request, dict)
        and isinstance(request["param"], Sequence)
        and len(request["param"]) > 1
    ):
        raise ValueError("Only one param is supported.")

    buffer_map = _load_buffer_map(source, request)
    [buffer] = buffer_map.values()
    return buffer.to_xarray()


def load(
    source: data_source.DataSource,
    request: Request,
) -> dict[str, xr.DataArray]:
    """Request data from a data source.

    Parameters
    ----------
    source : data_source.DataSource
        Source to request the data from.
    request : str | tuple[str, str] | dict[str, Any]
        Request for data from the source in the mars language.

    Raises
    ------
    RuntimeError
        when all of the requested data is not returned from the data source.

    Returns
    -------
    dict[str, xarray.DataArray]
        A mapping of shortName to data arrays of the requested fields.

    """
    buffer_map = _load_buffer_map(source, request)
    result = {}
    for name, buffer in buffer_map.items():
        try:
            result[name] = buffer.to_xarray()
        except MissingData as e:
            raise RuntimeError(f"Missing data for param: {name}") from e
    return result


class GribReader:
    def __init__(
        self,
        source: data_source.DataSource,
        ref_param: Request | None = None,
    ):
        """Initialize a grib reader from a data source.

        Parameters
        ----------
        source : data_source.DataSource
            Data source from which to retrieve the grib fields
        ref_param : str
            name of parameter used to construct a reference grid

        Raises
        ------
        ValueError
            if the grid can not be constructed from the ref_param

        """
        self.data_source = source
        if ref_param is not None:
            warn("GribReader: ref_param is deprecated.")

    @classmethod
    def from_files(cls, datafiles: list[Path], ref_param: Request | None = None):
        """Initialize a grib reader from a list of grib files.

        Parameters
        ----------
        datafiles : list[Path]
            List of grib input filenames
        ref_param : str
            name of parameter used to construct a reference grid

        Raises
        ------
        ValueError
            if the grid can not be constructed from the ref_param

        """
        return cls(data_source.DataSource([str(p) for p in datafiles]), ref_param)

    def _load_pv(self, pv_param: Request):
        fs = self.data_source.retrieve(pv_param)

        for field in fs:
            return field.metadata("pv")

    def load(
        self,
        requests: Mapping[str, Request],
        extract_pv: str | None = None,
    ) -> dict[str, xr.DataArray]:
        """Load a dataset with the requested parameters.

        Parameters
        ----------
        requests : Mapping[str, Request]
            Mapping of label to request for a given field from the data source.
        extract_pv: str | None
            Optionally extract hybrid level coefficients from the field referenced by
            the given label.

        Raises
        ------
        RuntimeError
            if not all fields are found in the data source.

        Returns
        -------
        dict[str, xr.DataArray]
            Mapping of fields by label

        """
        result = {
            name: tasking.delayed(load_single_param)(self.data_source, req)
            for name, req in requests.items()
        }

        if extract_pv is not None:
            if extract_pv not in requests:
                msg = f"{extract_pv=} was not a key of the given requests."
                raise RuntimeError(msg)
            return result | tasking.delayed(
                _extract_pv(self._load_pv(requests[extract_pv]))
            )

        return result

    def load_fieldnames(
        self,
        params: list[str],
        extract_pv: str | None = None,
    ) -> dict[str, xr.DataArray]:
        reqs = {param: param for param in params}
        return self.load(reqs, extract_pv)


def save(field: xr.DataArray, file_handle: io.BufferedWriter, bits_per_value: int = 16):
    """Write field to file in GRIB format.

    Parameters
    ----------
    field : xarray.DataArray
        Field to write into the output file.
    file_handle : io.BufferedWriter
        File handle for the output file.
    bits_per_value : int
        Bits per value encoded in the output file.

    Raises
    ------
    ValueError
        If the field does not have a message attribute.

    """
    if not hasattr(field, "message"):
        msg = "The message attribute is required to write to the GRIB format."
        raise ValueError(msg)

    stream = io.BytesIO(field.message)
    [md] = (f.metadata() for f in ekd.from_source("stream", stream))

    idx = {
        dim: field.coords[key]
        for key in field.dims
        if (dim := str(key)) not in {"x", "y"}
    }

    def to_grib(loc: dict[str, xr.DataArray]):
        return {INV_DIM_MAP[key]: value.item() for key, value in loc.items()}

    for idx_slice in product(*idx.values()):
        loc = {dim: value for dim, value in zip(idx.keys(), idx_slice)}
        array = field.sel(loc).values
        metadata = md.override(to_grib(loc))

        fs = ekd.FieldList.from_numpy(array, metadata)
        fs.write(file_handle, bits_per_value=bits_per_value)


def get_code_flag(value: int, indices: Sequence[int]) -> list[bool]:
    """Get the code flag value at the given indices.

    Parameters
    ----------
    value : int
        The code flag as an integer in the [0, 255] range.
    indices : Sequence[int]
        Indices at which to get the flag values. Left to right, 1-based.

    Returns
    -------
    list[bool]
        The code flag values at the given indices.

    """
    if not 0 <= value <= 255:
        raise ValueError("value must be a single byte integer")

    result = []
    for index in indices:
        if not 1 <= index <= 8:
            raise ValueError("index must in range [1,8]")
        shift = 8 - index
        result.append(bool(value >> shift & 1))
    return result


def set_code_flag(indices: Sequence[int]) -> int:
    """Create code flag by setting bits at the given indices.

    Parameters
    ----------
    indices : Sequence[int]
        Indices at which to set the flag values. Left to right, 1-based.

    Returns
    -------
    int
        Code flag with bits set at the given indices.

    """
    value = 0
    for index in indices:
        if not 1 <= index <= 8:
            raise ValueError("index must in range [1,8]")
        shift = 8 - index
        value |= 1 << shift
    return value
