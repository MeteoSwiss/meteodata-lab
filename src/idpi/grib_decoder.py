"""Decoder for grib data."""

# Standard library
import datetime as dt
import io
import typing
from collections.abc import Mapping, Sequence
from itertools import product
from pathlib import Path
from warnings import warn

# Third-party
import earthkit.data as ekd  # type: ignore
import numpy as np
import xarray as xr

# Local
from . import data_source, tasking

DIM_MAP = {
    "level": "z",
    "perturbationNumber": "eps",
    "step": "time",
}
INV_DIM_MAP = {v: k for k, v in DIM_MAP.items()}
VCOORD_TYPE = {
    "generalVertical": ("model_level", -0.5),
    "generalVerticalLayer": ("model_level", 0.0),
    "hybrid": ("hybrid", 0.0),
    "isobaricInPa": ("pressure", 0.0),
    "surface": ("surface", 0.0),
}

Request = str | tuple | dict


def _is_ensemble(field) -> bool:
    try:
        return field.metadata("typeOfEnsembleForecast") == 192
    except KeyError:
        return False


def _gather_coords(field_map, dims):
    coord_values = zip(*field_map)
    unique = (sorted(set(values)) for values in coord_values)
    coords = {dim: c for dim, c in zip(dims[:-2], unique)}
    ny, nx = next(iter(field_map.values())).shape
    shape = tuple(len(v) for v in coords.values()) + (ny, nx)
    return coords, shape


def _parse_datetime(date, time):
    return dt.datetime.strptime(f"{date}{time:04d}", "%Y%m%d%H%M")


def _gather_tcoords(time_meta):
    time = None
    valid_time = []
    for step in sorted(time_meta):
        tm = time_meta[step]
        valid_time.append(_parse_datetime(tm["validityDate"], tm["validityTime"]))
        if time is None:
            time = _parse_datetime(tm["dataDate"], tm["dataTime"])

    return {"valid_time": ("time", valid_time), "ref_time": time}


def _extract_pv(pv):
    if pv is None:
        return {}
    i = len(pv) // 2
    return {
        "ak": xr.DataArray(pv[:i], dims="z"),
        "bk": xr.DataArray(pv[i:], dims="z"),
    }


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

    def _construct_metadata(self, field: typing.Any):
        metadata: dict[str, typing.Any] = field.metadata(
            namespace=["geography", "parameter"]
        )
        # https://codes.ecmwf.int/grib/format/grib2/ctables/3/3/
        [vref_flag] = get_code_flag(field.metadata("resolutionAndComponentFlags"), [5])
        level_type: str = field.metadata("typeOfLevel")
        vcoord_type, zshift = VCOORD_TYPE.get(level_type, (level_type, 0.0))

        metadata |= {
            "vref": "native" if vref_flag else "geo",
            "vcoord_type": vcoord_type,
            "origin": {"z": zshift},
            "message": field.message(),
        }
        return metadata

    def _load_param(
        self,
        req: Request,
    ):
        fs = self.data_source.retrieve(req)

        hcoords: dict[str, xr.DataArray] = {}
        metadata: dict[str, typing.Any] = {}
        time_meta: dict[int, dict] = {}
        dims: tuple[str, ...] | None = None
        field_map: dict[tuple[int, ...], np.ndarray] = {}

        for field in fs:
            dim_keys = (
                ("perturbationNumber", "step", "level")
                if _is_ensemble(field)
                else ("step", "level")
            )
            key = field.metadata(*dim_keys)
            field_map[key] = field.to_numpy(dtype=np.float32)

            step = key[-2]  # assume all members share the same time steps
            if step not in time_meta:
                time_meta[step] = field.metadata(namespace="time")

            if not dims:
                dims = tuple(DIM_MAP[d] for d in dim_keys) + ("y", "x")

            if not metadata:
                metadata = self._construct_metadata(field)

            if not hcoords:
                hcoords = {
                    dim: xr.DataArray(dims=("y", "x"), data=values)
                    for dim, values in field.to_latlon().items()
                }

        if not field_map:
            raise RuntimeError(f"requested {req=} not found.")

        coords, shape = _gather_coords(field_map, dims)
        tcoords = _gather_tcoords(time_meta)

        array = xr.DataArray(
            np.array([field_map.pop(key) for key in sorted(field_map)]).reshape(shape),
            coords=coords | hcoords | tcoords,
            dims=dims,
            attrs=metadata,
        )

        return (
            array if array.vcoord_type != "surface" else array.squeeze("z", drop=True)
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
            name: tasking.delayed(self._load_param)(req)
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


def _get_type_of_level(field):
    if field.vcoord_type == "model_level":
        if field.origin["z"] == 0.0:
            return "generalVerticalLayer"
        elif field.origin["z"] == -0.5:
            return "generalVertical"
        else:
            raise ValueError(f"Unsupported field origin in z: {field.origin['z']}")
    else:
        mapping = {vc: name for name, (vc, _) in VCOORD_TYPE.items()}
        return mapping.get(field.vcoord_type, field.vcoord_type)


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
        result = {INV_DIM_MAP[key]: value.item() for key, value in loc.items()}
        return result | {"typeOfLevel": _get_type_of_level(field)}

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
