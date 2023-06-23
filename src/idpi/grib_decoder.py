"""Decoder for grib data."""
# Standard library
import os
from contextlib import contextmanager
from pathlib import Path

# Third-party
import earthkit.data  # type: ignore
import eccodes  # type: ignore
import numpy as np
import xarray as xr


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


def load_data(
    params: list[str], datafiles: list[Path], ref_param: str
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
    metadata = {}
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
        field_map[field.metadata(*dim_keys)] = field.to_numpy(dtype=np.float32)

        if param not in dims:
            dims[param] = dim_keys[:-1] + (field.metadata("typeOfLevel"), "y", "x")

        if param not in metadata:
            metadata[param] = field.metadata(
                namespace=["ls", "geography", "parameter", "time"]
            )

        if hcoords is None and param == ref_param:
            hcoords = {
                dim: (("y", "x"), values) for dim, values in field.to_points().items()
            }

    if not set(params) == data.keys():
        raise RuntimeError(f"Missing params: {set(params) - data.keys()}")

    result = {}
    for param, field_map in data.items():
        coords, shape = _gather_coords(field_map, dims[param])
        result[param] = xr.DataArray(
            np.array([field_map.pop(key) for key in sorted(field_map)]).reshape(shape),
            coords=coords | hcoords,
            dims=dims[param],
            attrs=metadata[param],
        )
    return result


def load_cosmo_data(
    params: list[str], datafiles: list[Path], ref_param: str = "HHL"
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
        return load_data(params, datafiles, ref_param)
