"""Decoder for grib data."""
# Standard library
import datetime as dt
import os
from contextlib import contextmanager
from importlib.resources import files
from pathlib import Path

# Third-party
import earthkit.data  # type: ignore
import eccodes  # type: ignore
import numpy as np
import xarray as xr
import yaml


@contextmanager
def cosmo_grib_defs():
    """Enable COSMO GRIB definitions."""
    prefix = os.environ["CONDA_PREFIX"]
    root_dir = Path(prefix) / "share"
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

    return {"valid_time": ("step", valid_time), "time": time}


def _extract_pv(pv):
    if pv is None:
        return {}
    i = len(pv) // 2
    return {
        "ak": xr.DataArray(pv[:i], dims="hybrid"),
        "bk": xr.DataArray(pv[i:], dims="hybrid"),
    }


def load_data(
    params: list[str],
    datafiles: list[Path],
    ref_param: str,
    extract_pv: str | None = None,
) -> dict[str, xr.DataArray]:
    """Load data from GRIB files.

    Parameters
    ----------
    params : list[str]
        List of fields to load from the data files.
    datafiles : list[Path]
        List of files from which to load the data.
    ref_param : str
        Parameter to use as a reference for the coordinates.
    extract_pv: str | None
        Optionally extract hybrid level coefficients from the given field.

    Raises
    ------
    ValueError
        if ref_param is not included in params.
    RuntimeError
        if not all fields are found in the given datafiles.

    Returns
    -------
    dict[str, xr.DataArray]
        Mapping of fields by param name

    """
    fs = earthkit.data.from_source("file", [str(p) for p in datafiles])

    if ref_param not in params:
        raise ValueError(f"{ref_param} must be in {params}")

    hcoords = None
    pv = None
    metadata = {}
    time_meta: dict[str, dict[int, dict]] = {}
    dims: dict[str, tuple[str, ...]] = {}
    data: dict[str, dict[tuple[int, ...], np.ndarray]] = {}
    for field in fs.sel(param=params):
        param = field.metadata("param")
        field_map = data.setdefault(param, {})
        dim_keys = (
            ("perturbationNumber", "step", "level")
            if _is_ensemble(field)
            else ("step", "level")
        )
        key = field.metadata(*dim_keys)
        field_map[key] = field.to_numpy(dtype=np.float32)

        step = key[-2]  # assume all members share the same time steps
        if step not in time_meta.get(param, {}):
            time_meta.setdefault(param, {})[step] = field.metadata(namespace="time")

        if param not in dims:
            dims[param] = dim_keys[:-1] + (field.metadata("typeOfLevel"), "y", "x")

        if param not in metadata:
            metadata[param] = field.metadata(namespace=["geography", "parameter"])

        if hcoords is None and param == ref_param:
            hcoords = {
                dim: (("y", "x"), values) for dim, values in field.to_points().items()
            }

        if extract_pv is not None and pv is None and param == extract_pv:
            # assume pv is constant in time and ensemble perturbations
            pv = field.metadata("pv")

    if not set(params) == data.keys():
        raise RuntimeError(f"Missing params: {set(params) - data.keys()}")

    result = {}
    for param, field_map in data.items():
        coords, shape = _gather_coords(field_map, dims[param])
        tcoords = _gather_tcoords(time_meta[param])
        result[param] = xr.DataArray(
            np.array([field_map.pop(key) for key in sorted(field_map)]).reshape(shape),
            coords=coords | hcoords | tcoords,
            dims=dims[param],
            attrs=metadata[param],
        )
    return result | _extract_pv(pv)


def load_cosmo_data(
    params: list[str],
    datafiles: list[Path],
    ref_param: str = "HHL",
    extract_pv: str | None = None,
) -> dict[str, xr.DataArray]:
    """Load data from GRIB files.

    The COSMO definitions are enabled during the load.

    Parameters
    ----------
    params : list[str]
        List of fields to load from the data files.
    datafiles : list[Path]
        List of files from which to load the data.
    ref_param : str
        Parameter to use as a reference for the coordinates.
    extract_pv: str | None
        Optionally extract hybrid level coefficients from the given field.

    Raises
    ------
    ValueError
        if ref_param is not included in params.
    RuntimeError
        if not all fields are found in the given datafiles.

    Returns
    -------
    dict[str, xr.DataArray]
        Mapping of fields by param name

    """
    with cosmo_grib_defs():
        return load_data(params, datafiles, ref_param, extract_pv)


def load_ifs_data(
    params: list[str],
    datafiles: list[Path],
    ref_param: str,
    extract_pv: str | None = None,
) -> dict[str, xr.DataArray]:
    """Load data from GRIB files.

    Expects IFS data.

    Parameters
    ----------
    params : list[str]
        List of fields to load from the data files.
    datafiles : list[Path]
        List of files from which to load the data.
    ref_param : str
        Parameter to use as a reference for the coordinates.
    extract_pv: str | None
        Optionally extract hybrid level coefficients from the given field.

    Raises
    ------
    ValueError
        if ref_param is not included in params.
    RuntimeError
        if not all fields are found in the given datafiles.

    Returns
    -------
    dict[str, xr.DataArray]
        Mapping of fields by param name

    """
    mapping_path = files("idpi.data").joinpath("field_mappings.yml")
    mapping = yaml.safe_load(mapping_path.open())
    missing = set(params) - mapping.keys()
    if missing:
        msg = f"Some params are not present in the field mappings: {missing}"
        raise ValueError(msg)
    params_map = {mapping[p]["ifs"]["name"]: p for p in params}

    def get_unit_factor(key):
        param = params_map.get(key)
        if param is None:
            return 1
        return mapping[param].get("cosmo", {}).get("unit_factor", 1)

    ifs_params = list(params_map.keys())
    ifs_ref_param = mapping[ref_param]["ifs"]["name"]
    ifs_extract_pv = (
        mapping[extract_pv]["ifs"]["name"] if extract_pv is not None else None
    )
    ds = load_data(ifs_params, datafiles, ifs_ref_param, ifs_extract_pv)
    with xr.set_options(keep_attrs=True):
        return {params_map.get(k, k): get_unit_factor(k) * v for k, v in ds.items()}
