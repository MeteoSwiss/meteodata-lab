"""Manage GRIB metadata."""

# Standard library
import dataclasses as dc
import typing

# Third-party
import numpy as np
import xarray as xr
from earthkit.data.core.metadata import Metadata

# Local
from . import grib_decoder

VCOORD_TYPE = {
    "generalVertical": ("model_level", -0.5),
    "generalVerticalLayer": ("model_level", 0.0),
    "isobaricInPa": ("pressure", 0.0),
}


def extract(metadata: Metadata):
    if metadata.get("gridType") == "unstructured_grid":
        vref_flag = False
    else:
        [vref_flag] = grib_decoder.get_code_flag(
            metadata.get("resolutionAndComponentFlags"), [5]
        )

    level_type = metadata.get("typeOfLevel")
    vcoord_type, zshift = VCOORD_TYPE.get(level_type, (level_type, 0.0))

    return {
        "parameter": metadata.as_namespace("parameter"),
        "geography": metadata.as_namespace("geography"),
        "vref": "native" if vref_flag else "geo",
        "vcoord_type": vcoord_type,
        "origin_z": zshift,
    }


def override(metadata: Metadata, **kwargs: typing.Any) -> dict[str, typing.Any]:
    """Override GRIB metadata.

    Note that no special consideration is made for maintaining consistency when
    overriding template definition keys such as productDefinitionTemplateNumber.
    Note that the origin components in x and y are left untouched.

    Parameters
    ----------
    metadata : Metadata
        Metadata of the input GRIB metadata
    kwargs : Any
        Keyword arguments forwarded to earthkit-data GribMetadata override method

    Returns
    -------
    dict[str, Any]
        Updated metadata along with the geography and parameter namespaces

    """

    if metadata["editionNumber"] == 1:
        return {
            "metadata": metadata,
            **extract(metadata),
        }

    md = metadata.override(**kwargs)

    return {
        "metadata": md,
        **extract(md),
    }


@dc.dataclass
class Grid:
    """Coordinates of the reference grid.

    Attributes
    ----------
    lon_first_grid_point: float
        longitude of first grid point in rotated lat-lon CRS
    lat_first_grid_point: float
        latitude of first grid point in rotated lat-lon CRS

    """

    lon_first_grid_point: float
    lat_first_grid_point: float


def load_grid_reference(metadata) -> Grid:
    """Construct a grid from a reference parameter.

    Parameters
    ----------
    metadata : Metadata
        GRIB metadata defining the reference grid.

    Returns
    -------
    Grid
        reference grid

    """
    return Grid(
        metadata["longitudeOfFirstGridPointInDegrees"],
        metadata["latitudeOfFirstGridPointInDegrees"],
    )


def compute_origin(ref_grid: Grid, field: xr.DataArray) -> dict[str, float]:
    """Compute horizontal components of the origin dict.

    Parameters
    ----------
    ref_grid : Grid
        reference grid
    field : xarray.DataArray
        field for which to compute the origin

    Returns
    -------
    dict[str, float]
        Horizontal components of the origin

    """
    x0 = ref_grid.lon_first_grid_point % 360
    y0 = ref_grid.lat_first_grid_point
    geo = field.geography
    dx = geo["iDirectionIncrementInDegrees"]
    dy = geo["jDirectionIncrementInDegrees"]
    x0_key = "longitudeOfFirstGridPointInDegrees"
    y0_key = "latitudeOfFirstGridPointInDegrees"

    return {
        "origin_x": np.round((geo[x0_key] % 360 - x0) / dx, 1),
        "origin_y": np.round((geo[y0_key] - y0) / dy, 1),
    }


def set_origin_xy(ds: dict[str, xr.DataArray], ref_param: str) -> None:
    """Set horizontal components of the origin attribute.

    Parameters
    ----------
    ds : dict[str, xarray.DataArray]
        Dataset of fields to update.
    ref_param : str
        Name of the parameter field to use as a reference. Must be a key of ds.

    Raises
    ------
    KeyError
        if the ref_param key is not found in the input dataset

    """
    if ref_param not in ds:
        raise KeyError(f"ref_param {ref_param} not present in dataset.")

    ref_grid = load_grid_reference(ds[ref_param].metadata)
    for field in ds.values():
        field.attrs |= compute_origin(ref_grid, field)


def extract_pv(metadata: Metadata) -> dict[str, xr.DataArray]:
    """Extract hybrid level coefficients.

    Parameters
    ----------
    message : Metadata
        GRIB metadata containing the pv metadata.

    Returns
    -------
    dict[str, xarray.DataArray]
        Hybrid level coefficients.

    """
    pv = metadata.get("pv")

    if pv is None:
        return {}

    i = len(pv) // 2
    return {
        "ak": xr.DataArray(pv[:i], dims="z"),
        "bk": xr.DataArray(pv[i:], dims="z"),
    }


def extract_hcoords(metadata: Metadata) -> dict[str, xr.DataArray]:
    """Extract horizontal coordinates.

    Parameters
    ----------
    metadata : Metadata
        GRIB metadata containing the grid definition.

    Returns
    -------
    dict[str, xarray.DataArray]
        Horizontal coordinates in geolatlon.

    """
    geo = metadata.geography
    return {
        "lat": xr.DataArray(dims=("y", "x"), data=geo.latitudes().reshape(geo.shape())),
        "lon": xr.DataArray(
            dims=("y", "x"), data=geo.longitudes().reshape(geo.shape())
        ),
    }
