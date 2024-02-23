"""Regridding operator."""

# Standard library
import dataclasses as dc
import typing

# Third-party
import numpy as np
import xarray as xr
from rasterio import transform, warp
from rasterio.crs import CRS

# Local
from .. import metadata
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
        if nx != int(nx) or ny != int(ny):
            raise ValueError("Inconsistent regrid parameters")
        return cls(crs, int(nx), int(ny), xmin, xmax, ymin, ymax)

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


def _udeg(value):
    return int(round(value * 1e6))


def _get_metadata(grid: RegularGrid):
    # geolatlon
    if grid.crs.to_epsg() == 4326:
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
        attrs |= metadata.override(field.message, **md)

    return xr.DataArray(data, attrs=attrs)
