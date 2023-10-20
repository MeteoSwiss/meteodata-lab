"""Decoder for grib data."""
# Standard library
import dataclasses as dc
import datetime as dt
import sys
import typing
from contextlib import contextmanager
from pathlib import Path

# Third-party
import earthkit.data  # type: ignore
import eccodes  # type: ignore
import numpy as np
import xarray as xr

# First-party
import idpi.config

# Local
from . import tasking
from .product import ProductDescriptor, Request

DIM_MAP = {
    "level": "z",
    "perturbationNumber": "eps",
    "step": "time",
}
VCOORD_TYPE = {
    "generalVertical": ("model_level", -0.5),
    "generalVerticalLayer": ("model_level", 0.0),
    "hybrid": ("hybrid", 0.0),
    "isobaricInPa": ("pressure", 0.0),
    "surface": ("surface", 0.0),
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
        Request("ak"): tasking.delayed(xr.DataArray(pv[:i], dims="z")),
        Request("bk"): tasking.delayed(xr.DataArray(pv[i:], dims="z")),
    }


@dc.dataclass
class Grid:
    """Coordinates of the reference grid.

    Attributes
    ----------
    lon: xr.DataArray
        2d array with longitude of geographical coordinates
    lat: xr.DataArray
        2d array with latitude of geographical coordinates
    lon_first_grid_point: float
        longitude of first grid point in rotated lat-lon CRS
    lat_first_grid_point: float
        latitude of first grid point in rotated lat-lon CRS

    """

    lon: xr.DataArray
    lat: xr.DataArray
    lon_first_grid_point: float
    lat_first_grid_point: float


class GribReader:
    def __init__(
        self,
        datafiles: list[Path],
        ref_param: str = "HHL",
        delay: bool = False,
    ):
        """Initialize a grib reader from a list of grib files.

        Parameters
        ----------
        datafiles : list[Path]
            List of grib input filenames
        ref_param : str
            name of parameter used to construct a reference grid
        delay : bool
            if True, it will (dask) delay the functions that load parameters

        Raises
        ------
        ValueError
            if the grid can not be constructed from the ref_param

        """
        self._datafiles = [str(p) for p in datafiles]
        if idpi.config.get("data_scope", "cosmo") == "cosmo":
            with cosmo_grib_defs():
                self._grid = self.load_grid_reference(ref_param)
        else:
            self._grid = self.load_grid_reference(ref_param)

    def load_grid_reference(self, ref_param: str) -> Grid:
        """Construct a grid from a reference parameter.

        Parameters
        ----------
        ref_param : str
            name of parameter used to construct a reference grid.

        Raises
        ------
        ValueError
            if ref_param is not found in the input dataset

        Returns
        -------
        Grid
            reference grid

        """
        fs = earthkit.data.from_source("file", self._datafiles)
        it = iter(fs.sel(param=ref_param))
        field = next(it, None)
        if field is None:
            msg = f"reference field, {ref_param=} not found in {self._datafiles=}"
            raise RuntimeError(msg)
        lonlat_dict = {
            geo_dim: xr.DataArray(dims=("y", "x"), data=values)
            for geo_dim, values in field.to_latlon().items()
        }

        grid = Grid(
            lonlat_dict["lon"],
            lonlat_dict["lat"],
            *field.metadata(
                "longitudeOfFirstGridPointInDegrees",
                "latitudeOfFirstGridPointInDegrees",
            ),
        )

        return grid

    def _load_pv(self, pv_param: str):
        fs = earthkit.data.from_source("file", self._datafiles).sel(param=pv_param)

        for field in fs:
            return field.metadata("pv")

    def _construct_metadata(self, field: typing.Any):
        metadata: dict[str, typing.Any] = field.metadata(
            namespace=["geography", "parameter"]
        )
        level_type: str = field.metadata("typeOfLevel")
        vcoord_type, zshift = VCOORD_TYPE.get(level_type, (level_type, 0.0))

        x0 = self._grid.lon_first_grid_point % 360
        y0 = self._grid.lat_first_grid_point
        geo = metadata["geography"]
        dx = geo["iDirectionIncrementInDegrees"]
        dy = geo["jDirectionIncrementInDegrees"]

        metadata |= {
            "vcoord_type": vcoord_type,
            "origin": {
                "z": zshift,
                "x": np.round(
                    (geo["longitudeOfFirstGridPointInDegrees"] % 360 - x0) / dx,
                    1,
                ),
                "y": np.round((geo["latitudeOfFirstGridPointInDegrees"] - y0) / dy, 1),
            },
        }
        return metadata

    def _load_param(
        self,
        req: Request,
    ):
        arg = {k: v for k, v in req._asdict().items() if v is not None}
        fs = earthkit.data.from_source("file", self._datafiles).sel(arg)

        hcoords = None
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

        if not field_map:
            raise RuntimeError(f"requested {req=} not found.")

        coords, shape = _gather_coords(field_map, dims)
        tcoords = _gather_tcoords(time_meta)
        hcoords = {
            "lon": self._grid.lon,
            "lat": self._grid.lat,
        }

        array = xr.DataArray(
            np.array([field_map.pop(key) for key in sorted(field_map)]).reshape(shape),
            coords=coords | hcoords | tcoords,
            dims=dims,
            attrs=metadata,
        )

        return (
            array if array.vcoord_type != "surface" else array.squeeze("z", drop=True)
        )

    def _load_dataset(
        self,
        reqs: typing.Iterable[Request],
        extract_pv: str | None = None,
    ) -> dict[Request, xr.DataArray]:
        params = {req.param for req in reqs}
        if extract_pv is not None and extract_pv not in params:
            raise ValueError(f"If set, {extract_pv=} must be in {params=}")

        result = {req: tasking.delayed(self._load_param)(req) for req in reqs}

        if not reqs == result.keys():
            raise RuntimeError(f"Missing params: {reqs - result.keys()}")

        if extract_pv:
            result = result | _extract_pv(self._load_pv(extract_pv))

        return result

    def load(
        self,
        descriptors: list[ProductDescriptor],
        extract_pv: str | None = None,
    ) -> dict[Request, xr.DataArray]:
        """Load a dataset with the requested parameters.

        Parameters
        ----------
        descriptors : list[ProductDescriptor]
            List of product descriptors from which the input fields required
            are extracted.
        extract_pv: str | None
            Optionally extract hybrid level coefficients from the given field.

        Raises
        ------
        RuntimeError
            if not all fields are found in the data source.

        Returns
        -------
        dict[Request, xr.DataArray]
            Mapping of fields by request

        """
        reqs = {req for desc in descriptors for req in desc.input_fields}

        return self.load_fields(reqs, extract_pv=extract_pv)

    def load_fieldnames(
        self,
        params: list[str],
        extract_pv: str | None = None,
    ) -> dict[str, xr.DataArray]:
        """Load a dataset with the requested parameters by name.

        Parameters
        ----------
        params : list[str]
            List of parameter names to include in the dataset.
        extract_pv: str | None
            Optionally extract hybrid level coefficients from the given field.

        Raises
        ------
        RuntimeError
            if not all fields are found in the data source.

        Returns
        -------
        dict[str, xr.DataArray]
            Mapping of fields by param name

        """
        desc = ProductDescriptor(input_fields=[Request(param) for param in params])
        result = self.load([desc], extract_pv=extract_pv)
        return {req.param: field for req, field in result.items()}

    def load_fields(
        self,
        params: typing.Iterable[Request],
        extract_pv: str | None = None,
    ) -> dict[Request, xr.DataArray]:
        """Load a dataset with the requested list of fields.

        Parameters
        ----------
        params : list[str]
            List of fields to load from the data files.
        extract_pv: str | None, optional
            Extract hybrid level coefficients from the given field.

        Raises
        ------
        RuntimeError
            if not all fields are found in the data source.

        Returns
        -------
        dict[Request, xr.DataArray]
            Mapping of fields by request

        """
        if idpi.config.get("data_scope", "cosmo") == "cosmo":
            if extract_pv:
                raise ValueError("extract_pv not supported with data_scope==cosmo")
            with cosmo_grib_defs():
                return self._load_dataset(params, extract_pv=None)
        else:
            return self._load_dataset(params, extract_pv=extract_pv)
