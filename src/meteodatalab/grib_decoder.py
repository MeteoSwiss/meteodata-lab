"""Decoder for grib data."""

# Standard library
import dataclasses as dc
import datetime as dt
import io
import logging
import typing
from collections import UserDict
from collections.abc import Callable, Mapping, Sequence
from enum import Enum
from itertools import product
from pathlib import Path
from uuid import UUID
from warnings import warn

# Third-party
import earthkit.data as ekd  # type: ignore
import numpy as np
import pandas as pd
import xarray as xr
from numpy.typing import DTypeLike

# Local
from . import data_source, icon_grid, mars, metadata, tasking
from .util import warn_deprecation

logger = logging.getLogger(__name__)

DIM_MAP = {
    "eps": "perturbationNumber",
    "ref_time": "ref_time",
    "lead_time": "step",
    "z": "level",
}
NAME_KEY = "shortName"

GeoCoordsCbk = Callable[[UUID], dict[str, xr.DataArray]]
Request = str | tuple | dict | mars.Request


class ChainMap(UserDict):
    def __init__(self, *maps):
        self._maps = maps

    def __getitem__(self, key):
        for mapping in self._maps:
            try:
                return mapping[key]
            except KeyError:
                pass
        raise KeyError(f"{key} not found")


class GribField(typing.Protocol):
    def metadata(self, *args, **kwargs) -> typing.Any: ...
    def message(self) -> bytes: ...
    def to_numpy(self, dtype: DTypeLike) -> np.ndarray: ...
    def to_latlon(self) -> dict[str, np.ndarray]: ...


class MissingData(RuntimeError):
    pass


class UnitOfTime(Enum):
    MINUTE = 0
    HOUR = 1
    DAY = 2
    SECOND = 13
    MISSING = 255

    @property
    def unit(self):
        if self.name == "MISSING":
            return None
        return self.name.lower()


def _is_ensemble(field) -> bool:
    try:
        return field.metadata("typeOfEnsembleForecast") == 192
    except KeyError:
        return False


def _get_hcoords(
    field: GribField, geo_coords: GeoCoordsCbk | None
) -> tuple[dict[str, xr.DataArray], tuple[str, ...]]:
    hdims: tuple[str, ...]
    if field.metadata("gridType") == "unstructured_grid":
        hdims = ("cell",)
        grid_uuid = UUID(field.metadata("uuidOfHGrid"))
        if geo_coords is None:
            logger.info(
                "No grid source provided when loading data with unstructured grid, "
                "falling back to balfrin grid file locations."
            )
            hcoords = icon_grid.load_grid_from_balfrin()(grid_uuid)
            return hcoords, hdims
        else:
            return geo_coords(grid_uuid), hdims

    hcoords = {
        dim: xr.DataArray(dims=("y", "x"), data=values)
        for dim, values in field.to_latlon().items()
    }
    hdims = ("y", "x")
    return hcoords, hdims


def _parse_datetime(date, time) -> dt.datetime:
    return dt.datetime.strptime(f"{date}{time:04d}", "%Y%m%d%H%M")


def _to_timedelta(value, unit) -> np.timedelta64:
    return pd.to_timedelta(value, unit).to_numpy()


def _get_key(field, dims):
    md = field.metadata()
    step = md["step"]
    unit = "h" if isinstance(step, int) else None
    extra = {
        "ref_time": _parse_datetime(md["dataDate"], md["dataTime"]),
        "step": _to_timedelta(step, unit),
    }
    dim_keys = (DIM_MAP[dim] for dim in dims)
    mapping = ChainMap(extra, md)
    return tuple(mapping[key] for key in dim_keys)


@dc.dataclass
class _FieldBuffer:
    is_ensemble: dc.InitVar[bool]
    dims: tuple[str, ...] = tuple(DIM_MAP)
    hdims: tuple[str, ...] = ("y", "x")
    hcoords: dict[str, xr.DataArray] = dc.field(default_factory=dict)
    metadata: dict[str, typing.Any] = dc.field(default_factory=dict)
    values: dict[tuple[int, ...], np.ndarray] = dc.field(default_factory=dict)

    def __post_init__(self, is_ensemble: bool):
        if not is_ensemble:
            self.dims = self.dims[1:]

    def load(self, field: GribField, geo_coords: GeoCoordsCbk | None) -> None:
        key = _get_key(field, self.dims)
        name = field.metadata(NAME_KEY)
        logger.debug("Received field for param: %s, key: %s", name, key)

        if key in self.values:
            logger.warn("Key collision for param: %s, key: %s", name, key)

        self.values[key] = field.to_numpy(dtype=np.float32)

        if not self.metadata:
            md = field.metadata().override()
            self.metadata = {
                "metadata": md,
                **metadata.extract(md),
            }

        if not self.hcoords:
            self.hcoords, self.hdims = _get_hcoords(field, geo_coords=geo_coords)

    def _gather_coords(self):
        coord_values = zip(*self.values)
        unique = (sorted(set(values)) for values in coord_values)
        coords = {dim: c for dim, c in zip(self.dims, unique)}

        if missing := [
            combination
            for combination in product(*coords.values())
            if combination not in self.values
        ]:
            msg = f"Missing combinations: {missing}"
            logger.exception(msg)
            raise RuntimeError(msg)

        field_shape = next(iter(self.values.values())).shape
        shape = tuple(len(v) for v in coords.values()) + field_shape
        return coords, shape

    def to_xarray(self) -> xr.DataArray:
        if not self.values:
            raise MissingData("No values.")

        coords, shape = self._gather_coords()
        ref_time = xr.DataArray(coords["ref_time"], dims="ref_time")
        lead_time = xr.DataArray(coords["lead_time"], dims="lead_time")
        tcoords = {"valid_time": ref_time + lead_time}

        array = xr.DataArray(
            data=np.array(
                [self.values.pop(key) for key in sorted(self.values)]
            ).reshape(shape),
            coords=coords | self.hcoords | tcoords,
            dims=self.dims + self.hdims,
            attrs=self.metadata,
        )

        if array.vcoord_type != "surface":
            return array

        return array.squeeze("z", drop=True)


def _load_buffer_map(
    source: data_source.DataSource,
    request: Request,
    geo_coords: GeoCoordsCbk | None,
) -> dict[str, _FieldBuffer]:
    logger.info("Retrieving request: %s", request)
    fs = source.retrieve(request)

    buffer_map: dict[str, _FieldBuffer] = {}

    for field in fs:
        name = field.metadata(NAME_KEY)
        if name in buffer_map:
            buffer = buffer_map[name]
        else:
            buffer = buffer_map[name] = _FieldBuffer(_is_ensemble(field))
        buffer.load(field, geo_coords=geo_coords)

    return buffer_map


def load_single_param(
    source: data_source.DataSource,
    request: Request,
    geo_coords: GeoCoordsCbk | None = None,
) -> xr.DataArray:
    """Request data from a data source for a single parameter.

    Parameters
    ----------
    source : data_source.DataSource
        Source to request the data from.
    request : str | tuple[str, str] | dict[str, Any] | meteodatalab.mars.Request
        Request for data from the source in the mars language.
    geo_coords: Callable[[UUID], dict[str, xr.DataArray]] | None
        Callable that returns the horizontal coordinates
        of the grid defined by the given UUID. The dimension must be "cell".

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

    buffer_map = _load_buffer_map(source, request, geo_coords)
    [buffer] = buffer_map.values()
    return buffer.to_xarray()


def load(
    source: data_source.DataSource,
    request: Request,
    geo_coords: GeoCoordsCbk | None = None,
) -> dict[str, xr.DataArray]:
    """Request data from a data source.

    Parameters
    ----------
    source : data_source.DataSource
        Source to request the data from.
    request : str | tuple[str, str] | dict[str, Any] | meteodatalab.mars.Request
        Request for data from the source in the mars language.
    geo_coords: Callable[[UUID], dict[str, xr.DataArray]] | None
        Callable that returns the horizontal coordinates
        of the grid defined by the given UUID. The dimension must be "cell".

    Raises
    ------
    RuntimeError
        when all of the requested data is not returned from the data source.

    Returns
    -------
    dict[str, xarray.DataArray]
        A mapping of shortName to data arrays of the requested fields.

    """
    buffer_map = _load_buffer_map(source, request, geo_coords=geo_coords)
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
        geo_coords: GeoCoordsCbk | None = None,
        ref_param: Request | None = None,
    ):
        """Initialize a grib reader from a data source.

        Parameters
        ----------
        source : data_source.DataSource
            Data source from which to retrieve the grib fields
        geo_coords: Callable[[UUID], dict[str, xr.DataArray]] | None
            Callable that returns the horizontal coordinates
            of the grid defined by the given UUID. The dimension must be "cell".
        ref_param : str
            name of parameter used to construct a reference grid

        Raises
        ------
        ValueError
            if the grid can not be constructed from the ref_param

        """
        warn_deprecation(
            "GribReader class will be removed in version 0.6. "
            "Use top level load function instead."
        )
        self.data_source = source
        self.geo_coords = geo_coords
        if ref_param is not None:
            warn("GribReader: ref_param is deprecated.")

    @classmethod
    def from_files(
        cls,
        datafiles: list[Path],
        geo_coords: GeoCoordsCbk | None = None,
        ref_param: Request | None = None,
    ):
        """Initialize a grib reader from a list of grib files.

        Parameters
        ----------
        datafiles : list[Path]
            List of grib input filenames
        geo_coords: Callable[[UUID], dict[str, xr.DataArray]] | None
            Callable that returns the horizontal coordinates
            of the grid defined by the given UUID. The dimension must be "cell".
        ref_param : str
            name of parameter used to construct a reference grid

        Raises
        ------
        ValueError
            if the grid can not be constructed from the ref_param

        """
        return cls(
            data_source.FileDataSource(datafiles=[str(p) for p in datafiles]),
            geo_coords,
            ref_param,
        )

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
            name: tasking.delayed(load_single_param)(
                self.data_source, req, self.geo_coords
            )
            for name, req in requests.items()
        }

        if extract_pv is not None:
            if extract_pv not in requests:
                msg = f"{extract_pv=} was not a key of the given requests."
                raise RuntimeError(msg)
            return result | metadata.extract_pv(result[extract_pv].metadata)
        return result

    def load_fieldnames(
        self,
        params: list[str],
        extract_pv: str | None = None,
    ) -> dict[str, xr.DataArray]:
        reqs = {param: param for param in params}
        return self.load(reqs, extract_pv)


def save(
    field: xr.DataArray,
    file_handle: io.BufferedWriter | io.BytesIO,
    bits_per_value: int = 16,
):
    """Write field to file in GRIB format.

    Parameters
    ----------
    field : xarray.DataArray
        Field to write into the output file.
    file_handle : io.BufferedWriter
        File handle for the output file.
    bits_per_value : int, optional
        Bits per value encoded in the output file. (Default: 16)

    Raises
    ------
    ValueError
        If the field does not have a metadata attribute.

    """
    if not hasattr(field, "metadata"):
        msg = "The metadata attribute is required to write to the GRIB format."
        raise ValueError(msg)

    md = field.metadata

    idx = {
        dim: field.coords[key]
        for key in field.dims
        if (dim := str(key)) not in {"x", "y", "cell"}
    }

    step_unit = UnitOfTime.MINUTE
    time_range_unit = UnitOfTime(md.get("indicatorOfUnitForTimeRange", 255)).unit
    time_range = _to_timedelta(md.get("lengthOfTimeRange", 0), unit=time_range_unit)

    if md.get("numberOfTimeRange", 1) != 1:
        raise NotImplementedError("Unsupported value for numberOfTimeRange")

    def to_grib(loc: dict[str, xr.DataArray]):
        grib_loc = {
            DIM_MAP[key]: value.item()
            for key, value in loc.items()
            if key not in {"ref_time", "lead_time"}
        }
        step_end = np.timedelta64(loc["lead_time"].item(), "ns")
        step_begin = step_end - time_range
        return grib_loc | {
            "indicatorOfUnitOfTimeRange": step_unit.value,
            "forecastTime": step_begin / _to_timedelta(1, step_unit.unit),
            "dataDate": loc["ref_time"].dt.strftime("%Y%m%d").item(),
            "dataTime": loc["ref_time"].dt.strftime("%H%M").item(),
        }

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
