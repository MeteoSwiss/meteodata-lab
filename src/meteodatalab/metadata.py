"""Manage GRIB metadata."""

# Standard library
import base64
import dataclasses as dc
import logging
import typing

# Third-party
import numpy as np
import xarray as xr
from earthkit.data import Field
from earthkit.data.field.grib.create import (
    create_grib_field_from_message,
)

# Local
from . import grib_decoder

_logger = logging.getLogger(__name__)


VCOORD_TYPE = {
    "generalVertical": ("model_level", -0.5),
    "generalVerticalLayer": ("model_level", 0.0),
    "isobaricInPa": ("pressure", 0.0),
}


def extract(field: Field) -> dict[str, typing.Any]:
    """Extract GRIB field metadata.

    Parameters
    ----------
    field : earthkit.data.Field
        GRIB field from which to extract metadata.

    Returns
    -------
    dict[str, Any]
        Dictionary containing parameter, geography, vref, vcoord_type,
        and origin_z metadata extracted from the field.

    """
    if field.metadata("gridType") == "unstructured_grid":
        vref_flag = False
    else:
        [vref_flag] = grib_decoder.get_code_flag(
            typing.cast(int, field.metadata("resolutionAndComponentFlags")), [5]
        )

    level_type = typing.cast(str, field.metadata("typeOfLevel"))
    vcoord_type, zshift = VCOORD_TYPE.get(level_type, (level_type, 0.0))

    md = typing.cast(
        dict[str, typing.Any],
        field.get(
            collections=["metadata.parameter", "metadata.geography"],
            output="dict",
        ),
    )
    return {
        "parameter": md["metadata.parameter"],
        "geography": md["metadata.geography"],
        "vref": "native" if vref_flag else "geo",
        "vcoord_type": vcoord_type,
        "origin_z": zshift,
        "uses_icon_grid": _uses_icon_grid(field),
        "uuidOfHGrid": field.get("metadata.uuidOfHGrid"),
    }


def serialise_field(field: Field) -> str:
    """Serialise a GRIB field to a base64-encoded string.

    Parameters
    ----------
    field : earthkit.data.Field
        GRIB field to serialise.

    Returns
    -------
    str
        Base64-encoded GRIB message.

    """
    message = field._get_grib().message(deflate=True)
    return base64.b64encode(message).decode()


def deserialise_field(value: str) -> Field:
    """Deserialise a base64-encoded GRIB message to a Field object.

    Parameters
    ----------
    value : str
        Base64-encoded GRIB message.

    Returns
    -------
    earthkit.data.Field
        GRIB field with no values loaded.

    """
    message = base64.b64decode(value.encode())
    return create_grib_field_from_message(message, no_values=True)


def override(message: str, **kwargs: typing.Any) -> dict[str, typing.Any]:
    """Override GRIB metadata.

    Note that no special consideration is made for maintaining consistency when
    overriding template definition keys such as productDefinitionTemplateNumber.

    Parameters
    ----------
    message : str
        Serialised GRIB message with original values
    kwargs : Any
        Metadata keys and values that are overridden in the output

    Returns
    -------
    dict[str, Any]
        Updated metadata along with the geography and parameter namespaces

    """
    field = deserialise_field(message)
    if field.metadata("editionNumber") == 1:
        return {
            "message_b64": message,
            **extract(field),
        }

    overrides = {f"metadata.{key}": value for key, value in kwargs.items()}
    result = field.set(overrides, sync=True)

    if result is None:
        raise RuntimeError("failed to override metadata")

    return {
        "message_b64": serialise_field(result),
        **extract(result),
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


def load_grid_reference(field: Field) -> Grid:
    """Construct a grid from a reference parameter.

    Parameters
    ----------
    field : earthkit.data.Field
        Field defining the reference grid.

    Returns
    -------
    Grid
        reference grid

    """
    return Grid(
        field.metadata("longitudeOfFirstGridPointInDegrees"),
        field.metadata("latitudeOfFirstGridPointInDegrees"),
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


def _uses_icon_grid(field: Field) -> bool:
    """Determine if the data is on a MeteoSwiss ICON grid.

    Parameters
    ----------
    field : earthkit.data.Field
        Field containing the grid definition.

    Returns
    -------
    bool
        True if the data was created by an MCH ICON forecast.

    """
    return (
        field.metadata("centre") == "lssw"
        and field.metadata("generatingProcessIdentifier") in (141, 142)
        and field.metadata("gridType") == "unstructured_grid"
    )


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

    ref_field = deserialise_field(ds[ref_param].message_b64)

    if _uses_icon_grid(ref_field):
        _logger.warning(
            "Data is on the ICON grid, not setting origin values. "
            "Setting the origin components is intended for support with horizontal "
            "grid staggering, which is not used in the output of the ICON model."
        )
        return

    ref_grid = load_grid_reference(ref_field)
    for field in ds.values():
        field.attrs |= compute_origin(ref_grid, field)


def extract_hcoords(message_b64: str) -> dict[str, xr.DataArray]:
    """Extract horizontal coordinates.

    Parameters
    ----------
    message_b64 : str
        Serialised GRIB message containing the grid definition.

    Returns
    -------
    dict[str, xarray.DataArray]
        Horizontal coordinates in geolatlon.

    """
    field = deserialise_field(message_b64)
    lat, lon = field.geography.latlons()
    return {
        "lat": xr.DataArray(dims=("y", "x"), data=lat),
        "lon": xr.DataArray(dims=("y", "x"), data=lon),
    }


def is_staggered_horizontal(field: xr.DataArray) -> bool:
    """Determine if the field is on a staggered horizontal grid.

    Parameters
    ----------
    field: xr.DataArray
        Field containing the grid definition.

    Raises
    ------
    ValueError
        if the field is a on regular grid without origin_x and origin_y set.

    Returns
    -------
    bool
        True if the field is on a staggered horizontal grid.

    """
    if field.attrs.get("uses_icon_grid", False):
        return False

    if "origin_x" not in field.attrs or "origin_y" not in field.attrs:
        raise ValueError("Field is missing origin, run set_origin_xy on the data set.")
    return field.origin_x != 0.0 or field.origin_y != 0.0
