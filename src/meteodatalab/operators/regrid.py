"""Regridding operator."""

# Standard library
import dataclasses as dc
import typing
import warnings
from typing import Literal

# Third-party
import numpy as np
import xarray as xr
from numpy.typing import ArrayLike, NDArray

try:
    # Third-party
    from pyproj import Transformer
    from rasterio import transform, warp
    from rasterio.crs import CRS
    from scipy.spatial import Delaunay  # type: ignore
except ImportError:
    raise ImportError("The regrid operator requires extra dependencies.")

# Local
from .. import icon_grid, metadata, util
from ..grib_decoder import set_code_flag

Resampling: typing.TypeAlias = warp.Resampling

# For more information: check https://epsg.io/<id>
CRS_ALIASES = {
    "geolatlon": "epsg:4326",  # WGS84
    "swiss": "epsg:21781",  # Swiss CH1903 / LV03
    "swiss03": "epsg:21781",  # Swiss CH1903 / LV03
    "swiss95": "epsg:2056",  # Swiss CH1903+ / LV95
    "boaga-west": "epsg:3003",  # Monte Mario / Italy zone 1
    "boaga-east": "epsg:3004",  # Monte Mario / Italy zone 2
    "utm32n": "epsg:32632",  # Universal Transverse Mercator zone 32N
}


def _get_crs(geo):
    if geo["gridType"] != "rotated_ll":
        raise NotImplementedError("Unsupported grid type")

    lon = geo["longitudeOfSouthernPoleInDegrees"]
    lat = -1 * geo["latitudeOfSouthernPoleInDegrees"]

    return CRS.from_string(
        f"+proj=ob_tran +o_proj=longlat +o_lat_p={lat} +lon_0={lon} +datum=WGS84"
    )


def _normalise(angle: float) -> float:
    return np.fmod(angle + 180, 360) - 180


@dc.dataclass
class RegularGrid:
    """Class defining a regular grid.

    Attributes
    ----------
    crs : CRS
        Coordinate reference system.
    nx : int
        Number of grid points in the x direction.
    ny : int
        Number of grid points in the y direction.
    xmin : float
        Coordinate of the first grid point in the x direction.
    xmax : float
        Coordinate of the last grid point in the x direction.
    ymin : float
        Coordinate of the first grid point in the y direction.
    ymax : float
        Coordinate of the last grid point in the y direction.

    """

    crs: CRS
    nx: int
    ny: int
    xmin: float
    xmax: float
    ymin: float
    ymax: float

    @classmethod
    def from_field(cls, field: xr.DataArray):
        """Extract grid parameters from grib metadata.

        Parameters
        ----------
        field : xarray.DataArray
            field containing the relevant metadata.

        """
        geo = field.geography
        obj = cls(
            crs=_get_crs(geo),
            nx=geo["Ni"],
            ny=geo["Nj"],
            xmin=_normalise(geo["longitudeOfFirstGridPointInDegrees"]),
            xmax=_normalise(geo["longitudeOfLastGridPointInDegrees"]),
            ymin=geo["latitudeOfFirstGridPointInDegrees"],
            ymax=geo["latitudeOfLastGridPointInDegrees"],
        )
        if abs(obj.dx - geo["iDirectionIncrementInDegrees"]) > 1e-5:
            raise ValueError("Inconsistent grid parameters")
        if abs(obj.dy - geo["jDirectionIncrementInDegrees"]) > 1e-5:
            raise ValueError("Inconsistent grid parameters")
        return obj

    @classmethod
    def parse_regrid_operator(cls, op: str):
        """Parse fieldextra out_regrid_target string.

        Parameters
        ----------
        op : str
            fieldextra out_regrid_target definition
            i.e. crs,xmin,ymin,xmay,ymax,dx,dy.

        """
        crs_str, *grid_params = op.split(",")
        crs = CRS.from_string(CRS_ALIASES[crs_str])
        xmin, ymin, xmax, ymax, dx, dy = map(float, grid_params)
        if abs(dx) < 1e-10 or abs(dy) < 1e-10:
            raise ValueError("Inconsistent regrid parameters")
        nx = (xmax - xmin) / dx + 1
        ny = (ymax - ymin) / dy + 1
        if abs(nx - round(nx)) > 1e-10 or abs(ny - round(ny)) > 1e-10:
            raise ValueError("Inconsistent regrid parameters")
        return cls(crs, int(round(nx)), int(round(ny)), xmin, xmax, ymin, ymax)

    def to_crs(self, crs: str, **kwargs):
        """Return a new grid in the given coordinate reference system.

        Parameters
        ----------
        crs : str
            The coordinate reference system in which the output grid should be defined.

        Returns
        -------
        RegularGrid or subtype
            Output grid in the given coordinate reference system.

        """
        dst_crs = CRS.from_string(crs)
        tx, width, height = typing.cast(
            tuple[transform.Affine, int, int],
            warp.calculate_default_transform(
                src_crs=self.crs,
                dst_crs=dst_crs,
                width=self.nx,
                height=self.ny,
                left=self.xmin,
                bottom=self.ymin,
                right=self.xmax,
                top=self.ymax,
                **kwargs,
            ),
        )
        a = transform.AffineTransformer(tx)
        xmin, ymax = a.xy(-0.5, -0.5)
        xmax, ymin = a.xy(height + 0.5, width + 0.5)  # row, col
        return type(self)(dst_crs, width, height, xmin, xmax, ymin, ymax)

    @property
    def x(self) -> np.ndarray:
        return np.arange(self.nx) * self.dx + self.xmin

    @property
    def y(self) -> np.ndarray:
        return np.arange(self.ny) * self.dy + self.ymin

    @property
    def dx(self) -> float:
        return (self.xmax - self.xmin) / (self.nx - 1)

    @property
    def dy(self) -> float:
        return (self.ymax - self.ymin) / (self.ny - 1)

    @property
    def transform(self) -> transform.Affine:
        return transform.from_origin(
            west=self.xmin - self.dx / 2,
            north=self.ymax + self.dy / 2,
            xsize=self.dx,
            ysize=self.dy,
        )


def _udeg(value: float) -> int:
    return int(round(value * 1e6))


def _lon_from_utm_zone(zone: int) -> int:
    if zone is None or zone < 1 or zone > 60:
        raise ValueError(f"Invalid value for UTM zone: {zone}.")

    # UTM zone are 6 degrees wide numbered from 1 starting at -180 to -174 degrees.
    offset = zone * 6
    return offset - 183


def _grib_utm_m(value: float | int) -> int:
    # For UTM units, GRIB2 uses 10-2m whereas CRS uses m.
    return int(round(100 * value))


def _get_metadata(grid: RegularGrid):
    if grid.crs.to_epsg() == 4326:
        # geolatlon
        # https://codes.ecmwf.int/grib/format/grib2/ctables/3/4/
        scanning_mode = set_code_flag([2])  # positive y
        # i, j direction increments given
        # bit 5 left unset since the target grid is geolatlon
        # both values are equivalent in this case
        resolution_components_flags = set_code_flag([3, 4])
        return {
            "numberOfDataPoints": grid.nx * grid.ny,
            "sourceOfGridDefinition": 0,  # defined by template number
            "numberOfOctectsForNumberOfPoints": 0,
            "interpretationOfNumberOfPoints": 0,
            "gridDefinitionTemplateNumber": 0,  # latlon
            "shapeOfTheEarth": 5,  # WGS 84
            "Ni": grid.nx,
            "Nj": grid.ny,
            "latitudeOfFirstGridPoint": _udeg(grid.ymin),
            "longitudeOfFirstGridPoint": _udeg(grid.xmin),
            "resolutionAndComponentFlags": resolution_components_flags,
            "latitudeOfLastGridPoint": _udeg(grid.ymax),
            "longitudeOfLastGridPoint": _udeg(grid.xmax),
            "iDirectionIncrement": _udeg(grid.dx),
            "jDirectionIncrement": _udeg(grid.dy),
            "scanningMode": scanning_mode,
        }
    elif grid.crs.get("proj") == "utm" and not grid.crs.get("south"):
        # Transverse Mercator in northern hemisphere.
        # https://codes.ecmwf.int/grib/format/grib2/ctables/3/4/
        scanning_mode = set_code_flag([2])  # positive y
        # i, j direction increments given relative to defined grid.
        resolution_components_flags = set_code_flag([3, 4, 5])
        return {
            "numberOfDataPoints": grid.nx * grid.ny,
            "sourceOfGridDefinition": 0,  # defined by template number
            "numberOfOctectsForNumberOfPoints": 0,
            "interpretationOfNumberOfPoints": 0,
            "gridDefinitionTemplateNumber": 12,  # UTM
            "shapeOfTheEarth": 5,  # WGS 84
            "Ni": grid.nx,
            "Nj": grid.ny,
            "falseEasting": _grib_utm_m(500000),
            "falseNorthing": 0,  # Northern hemisphere
            "scaleFactorAtReferencePoint": 0.9996,
            "longitudeOfReferencePoint": _lon_from_utm_zone(grid.crs.get("zone")),
            "Di": _grib_utm_m(grid.dx),
            "Dj": _grib_utm_m(grid.dy),
            "X1": _grib_utm_m(grid.xmin),
            "X2": _grib_utm_m(grid.xmax),
            "Y1": _grib_utm_m(grid.ymin),
            "Y2": _grib_utm_m(grid.ymax),
            "resolutionAndComponentFlags": resolution_components_flags,
            "scanningMode": scanning_mode,
        }
    elif grid.crs.get("proj") == "ob_tran":
        # rotlatlon
        # https://codes.ecmwf.int/grib/format/grib2/ctables/3/4/
        scanning_mode = set_code_flag([2])  # positive y
        # i, j direction increments given
        resolution_components_flags = set_code_flag([3, 4])
        return {
            "numberOfDataPoints": grid.nx * grid.ny,
            "sourceOfGridDefinition": 0,  # defined by template number
            "numberOfOctectsForNumberOfPoints": 0,
            "interpretationOfNumberOfPoints": 0,
            "gridDefinitionTemplateNumber": 1,  # rotlatlon
            "shapeOfTheEarth": 5,  # WGS 84
            "Ni": grid.nx,
            "Nj": grid.ny,
            "latitudeOfFirstGridPoint": _udeg(grid.ymin),
            "longitudeOfFirstGridPoint": _udeg(grid.xmin),
            "resolutionAndComponentFlags": resolution_components_flags,
            "latitudeOfLastGridPoint": _udeg(grid.ymax),
            "longitudeOfLastGridPoint": _udeg(grid.xmax),
            "iDirectionIncrement": _udeg(grid.dx),
            "jDirectionIncrement": _udeg(grid.dy),
            "scanningMode": scanning_mode,
            "latitudeOfSouthernPole": _udeg(-1 * grid.crs.get("o_lat_p")),
            "longitudeOfSouthernPole": _udeg(grid.crs.get("lon_0")),
            "angleOfRotation": 0.0,
        }
    else:
        # Rather than attempt to populate the GRIB definition in the general case, we
        # just set the sourceOfGridDefinition to 255. Ideally we would also set
        # gridDefinitionTemplateNumber to 65535, but eccodes attempts and fails to find
        # a template by this number.
        return {
            "sourceOfGridDefinition": 255,  # grid definition does not apply
            "numberOfDataPoints": grid.nx * grid.ny,
            "numberOfOctectsForNumberOfPoints": 0,
        }


def regrid(
    field: xr.DataArray,
    dst: RegularGrid,
    resampling: Resampling,
    src: RegularGrid | None = None,
):
    """Regrid a field.

    Parameters
    ----------
    field : xarray.DataArray
        Input field defined on a regular grid in rotated latlon coordinates.
    dst : RegularGrid
        Destination grid onto which to project the field.
    resampling : Resampling
        Resampling method, alias of rasterio.warp.Resampling.
    src : RegularGrid, optional
        Definition of the input field grid

    Raises
    ------
    ValueError
        If the input field is not defined on a regular grid in rotated latlon or
        if the input field geography metadata does not have consistent grid parameters.

    Returns
    -------
    xarray.DataArray
        Field regridded in the destination grid.

    """
    if src is None:
        src = RegularGrid.from_field(field)

    def reproject_layer(field):
        output = np.zeros((dst.ny, dst.nx))
        warp.reproject(
            source=field[::-1],
            destination=output,
            src_crs=src.crs,
            src_transform=src.transform,
            dst_crs=dst.crs,
            dst_transform=dst.transform,
            resampling=resampling,
        )
        return output[::-1]

    # output dims renamed to workaround limitation that overlapping dims in the input
    # must not change in size
    data = xr.apply_ufunc(
        reproject_layer,
        field,
        input_core_dims=[["y", "x"]],
        output_core_dims=[["y1", "x1"]],
        vectorize=True,
    ).rename({"x1": "x", "y1": "y"})

    attrs = field.attrs
    if md := _get_metadata(dst):
        attrs = attrs | metadata.override(field.metadata, **md)

    return xr.DataArray(data, attrs=attrs)


def _icon2regular(
    field: xr.DataArray, dst: RegularGrid, indices: np.ndarray, weights: np.ndarray
) -> xr.DataArray:
    mask = np.all(indices != 0, axis=-1)

    def reproject_layer(field):
        out_shape = field.shape[:-1] + (dst.ny, dst.nx)
        values = np.take(field, indices, axis=-1)
        if np.any(np.isnan(values)):
            warnings.warn("Interpolation of missing values is not supported.")
        vmin = np.min(values, axis=-1)
        vmax = np.max(values, axis=-1)
        result = np.einsum("...ij,ij->...i", values, weights)
        masked = np.where(mask, result, np.nan)
        return np.clip(masked, vmin, vmax).reshape(out_shape)

    data = xr.apply_ufunc(
        reproject_layer,
        field,
        input_core_dims=[["cell"]],
        output_core_dims=[["y", "x"]],
    )

    attrs = field.attrs
    if md := _get_metadata(dst):
        attrs = attrs | metadata.override(field.metadata, **md)

    return xr.DataArray(data, attrs=attrs)


def icon2geolatlon(field: xr.DataArray) -> xr.DataArray:
    """Remap ICON native grid data to the geolatlon grid.

    The interpolation is done with pre-computed weights based on the RBF
    interpolation method as implemented in icon-tools from the DWD.

    Parameters
    ----------
    field : xarray.DataArray
        A field with data in the ICON native grid.

    Returns
    -------
    xarray.DataArray
        Field with data remapped to the geolatlon grid.

    """
    gid = field.metadata.get("uuidOfHGrid")
    coeffs = icon_grid.get_remap_coeffs(gid, "geolatlon")
    indices = coeffs["rbf_B_glbidx"].values
    weights = coeffs["rbf_B_wgt"].values

    dst = RegularGrid(
        crs=CRS.from_string("epsg:4326"),
        nx=coeffs.nx,
        ny=coeffs.ny,
        xmin=coeffs.xmin,
        ymin=coeffs.ymin,
        xmax=coeffs.xmax,
        ymax=coeffs.ymax,
    )

    return _icon2regular(field, dst, indices, weights)


def icon2rotlatlon(field: xr.DataArray) -> xr.DataArray:
    """Remap ICON native grid data to the rotated latlon grid.

    The interpolation is done with pre-computed weights based on the RBF
    interpolation method as implemented in icon-tools from the DWD.

    Parameters
    ----------
    field : xarray.DataArray
        A field with data in the ICON native grid.

    Returns
    -------
    xarray.DataArray
        Field with data remapped to the rotated latlon grid.

    """
    gid = field.metadata.get("uuidOfHGrid")
    coeffs = icon_grid.get_remap_coeffs(gid, "rotlatlon")
    indices = coeffs["rbf_B_glbidx"].values
    weights = coeffs["rbf_B_wgt"].values

    geo = {
        "gridType": "rotated_ll",
        "longitudeOfSouthernPoleInDegrees": coeffs.north_pole_lon - 180,
        "latitudeOfSouthernPoleInDegrees": -1 * coeffs.north_pole_lat,
    }
    dst = RegularGrid(
        crs=_get_crs(geo),
        nx=coeffs.nx,
        ny=coeffs.ny,
        xmin=coeffs.xmin,
        ymin=coeffs.ymin,
        xmax=coeffs.xmax,
        ymax=coeffs.ymax,
    )

    return _icon2regular(field, dst, indices, weights)


def _linear_weights(pts_src: ArrayLike, pts_dst: ArrayLike) -> tuple[NDArray, NDArray]:
    """Compute indices and weights for barycentric linear interpolation."""
    tri = Delaunay(pts_src)
    simplex = tri.find_simplex(pts_dst)
    isfound = simplex != -1
    vertices = np.take(tri.simplices, simplex, axis=0)
    indices = np.where(isfound[:, None], vertices, 0)

    # note that zero is a valid index
    # however, a full line of zeros is interpreted as out of bounds
    # in the interpolation step

    temp = np.take(tri.transform, simplex, axis=0)
    delta = pts_dst - temp[:, 2]
    bary = np.einsum("njk,nk->nj", temp[:, :2, :], delta)
    wgts = np.hstack((bary, 1 - bary.sum(axis=1, keepdims=True)))
    weights = np.where(isfound[:, None], wgts, 0)

    return indices, weights


def _linear_weights_cropped_domain(
    pts_src: NDArray, pts_dst: NDArray, buffer: float = 4e3
) -> tuple[NDArray, NDArray]:
    """Compute linear interpolation weights from a cropped source grid.

    Crops the source grid to a box with a buffer outside of the destination grid. The
    default buffer is 4 km when using a meter-based coordinate system.

    Both pts_src and pts_dst are expected to be rank 2 arrays representing a list of
    points using the same coordinate system.
    """
    xmin, ymin = np.min(pts_dst, axis=0) - buffer
    xmax, ymax = np.max(pts_dst, axis=0) + buffer
    x, y = np.transpose(pts_src)
    mask = (xmin < x) & (x < xmax) & (ymin < y) & (y < ymax)
    [idx] = np.nonzero(mask)
    indices, weights = _linear_weights(pts_src[idx], pts_dst)
    return idx[indices], weights


def _key_maker(field: xr.DataArray, dst: RegularGrid) -> tuple[str, str] | None:
    md5 = field.metadata.get("md5Section3", None)
    if md5 is None:
        return None
    return md5, repr(dst)


@util.memoize(_key_maker)
def _compute_barycentric_weights(
    field: xr.DataArray, dst: RegularGrid
) -> tuple[NDArray, NDArray]:
    utm_crs = "epsg:32632"  # UTM zone 32N

    transformer_src = Transformer.from_crs("epsg:4326", utm_crs, always_xy=True)
    points_src = transformer_src.transform(field.lon, field.lat)

    gx, gy = np.meshgrid(dst.x, dst.y)
    transformer_dst = Transformer.from_crs(dst.crs.wkt, utm_crs, always_xy=True)
    points_dst = transformer_dst.transform(gx.flat, gy.flat)

    xy = np.array(points_src).T
    uv = np.array(points_dst).T

    return _linear_weights_cropped_domain(xy, uv)


def iconremap(
    field: xr.DataArray, dst: RegularGrid, method: Literal["byc"] = "byc"
) -> xr.DataArray:
    """Remap ICON native grid data to a regular grid.

    Note that the interpolation method is linear.

    Parameters
    ----------
    field : xarray.DataArray
        A field with data in the ICON native grid.
    dst : RegularGrid
        A regular grid in any coordinate system.
    method : Literal["byc"]
        Method used to perform the interpolation.

        Available methods:
        - byc: Barycentric linear interpolation.

    Returns
    -------
    xarray.DataArray
        Field with data remapped to the given swiss grid.

    """
    if method not in {"byc"}:
        raise NotImplementedError(f"method: {method} is not implemented")

    indices, weights = _compute_barycentric_weights(field, dst)

    gx, gy = np.meshgrid(dst.x, dst.y)
    transformer_geo = Transformer.from_crs(dst.crs.wkt, "epsg:4326", always_xy=True)
    lon, lat = transformer_geo.transform(gx, gy)

    return _icon2regular(field, dst, indices, weights).assign_coords(
        lon=(("y", "x"), lon), lat=(("y", "x"), lat)
    )
