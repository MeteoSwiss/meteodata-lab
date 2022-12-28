"""Vertical reduction operators."""

from lib2to3.pytree import HUGE

import numpy as np
import xarray as xr
from operators.destagger import destagger


def reduce_k(field, operator, mode, height, h_bounds, hsurf=None):
    """Reduce a field given on k levels on some height interval.

    Parameters
    ----------
    field : xarray.DataArray
        field to reduce, defined either on model layer mid surfaces (typeOfLevel="generalVerticalLayer")
        or on model layer surfaces (typeOfLevel="generalVertical")
    height : xarray.DataArray
        if operator in ("integral", "normed_integral"):
            height field on model layer surfaces (typeOfLevel="generalVertical")
        if operator in ("minimum", "maximum"):
            height field defined on the same typeOfLevel as the field to reduce
    operator : str
        reduction operator, possible values are
        "integral", "normed_integral", maximum", "minimum"
    mode : str
        defintion mode for height interval boundaries, possible values are
        "h2h": height agl to height agl
        "h2z": height agl to height amsl
        "z2h": height amsl to height agl
        "z2z": height amsl to height amsl
    h_bounds : list of xarray.DataArray of length 2
        height interval bounds (surface level field or single level of a multi-level field)
    hsurf : Optional(xarray.DataArray)
        earth surface height in m asl
        required if mode is one of {"h2h", "h2z", "z2h"}

    Returns
    -------
    rfield : xarray.DataArray
        reduced field

    """
    # Note on multilevel results
    # z2z: h_bounds elements refer to single level of a height field
    # z2h: h_bounds elements refer to single level of a height field
    # h2h: h_bounds elements refer to single level of a height field
    # h2z: h_bounds elements refer to single level of a height field
    # TODO: add some checks on level types of input fields, and on values and order of h_bounds

    # Parameters
    # ... supported reduction operators
    reduction_operators = ("integral", "normed_integral", "maximum", "minimum")
    # ... supported height interval modes
    height_interval_modes = ("h2h", "h2z", "z2h", "z2z")

    # Check arguments
    # ... operator
    if operator not in reduction_operators:
        raise RuntimeError("reduce_k: unsupported operator ", operator)
    # ... mode
    if mode not in height_interval_modes:
        raise RuntimeError("reduce_k: unsupported mode ", mode)
    # ... hsurf
    if mode in ["h2z", "z2h", "h2h"] and hsurf is None:
        raise RuntimeError(
            "reduce_k: hsurf is required when using operator ",
            operator,
            "with mode ",
            mode,
        )

    # Height bounds are always converted to heights amsl; lower_bound_type and upper_bound_type
    # can be used to code typeOfFirstFixedSurface and typeOfSecondFixedSurface in GRIB2, and
    # to set the bounds attribute for the vertical coordinates in NetCDF
    h_bottom = h_bounds[0].copy()
    h_top = h_bounds[1].copy()
    if mode in ["h2z", "h2h"]:
        # ... convert lower bound to height amsl
        h_bottom += hsurf
    if mode in ["z2h", "h2h"]:
        # ... convert upper bound to height amsl
        h_top += hsurf

    # Find height interval including the interval [h_bottom, h_top]
    # ... integral: approximated by midpoint rule, taking into account that h_bottom and h_top, respectively,
    #               may not coincide with a model layer interface;
    #               if typeOfLevel(f)="generalVerticalLayer":
    #                       f(kstart)[h_top - hhl(kstart+1)] + sum(k=kstart+1,kstop-1)f(k)[hhl(k)-hhl(k+1)] + f(kstop)[hhl(kstop) - h_bottom]
    #               if typeOfLevel(f)="generalVertical"
    #                       0.5*[f(kstart+1) + f(kstart)][h_top - hhl(kstart+1)]
    #                       + sum(k=kstart+1,kstop-1)0.5*[f(k+1)+f(k)][hhl(k)-hhl(k+1)]
    #                       + 0.5*[f(kstop)+f(kstop+1)][hhl(kstop) - h_bottom]
    #               kstart and kstop refer to all model midpoint surfaces included in the height interval.
    # ... normed_integral: integral / (h_top - h_bottom)
    # ... maximum/minimum: extremum over the field values at all model levels included in the height interval, and at the interval boundaries
    #     after linear interpolation wrt height; f and auxiliary height fields must either both be defined on full levels or half levels

    if operator in ["integral", "normed_integral"]:
        if "generalVertical" in field.coords:
            field_on_fl = destagger(field, "generalVertical")
        else:
            field_on_fl = field
        if "generalVertical" not in height.coords:
            raise RuntimeError(
                "reduce_k: height must be defined on level type generalVertical"
            )
        # ... prepare the height hfl of model mid layer surfaces (needed to select the field values within [h_bottom, h_top])
        hfl = destagger(height, "generalVertical")
        # .. prepare dh = height(k) - height(k+1), defined on model mid layer surfaces
        hhlk = xr.full_like(hfl, np.nan)
        hhlkp1 = xr.full_like(hfl, np.nan)
        hhlk[{"generalVerticalLayer": slice(0, None)}] = height[
            {"generalVertical": slice(0, -1)}
        ]
        hhlkp1[{"generalVerticalLayer": slice(0, None)}] = height[
            {"generalVertical": slice(1, None)}
        ]
        dh = xr.where((hhlk > h_top) & (hhlkp1 < h_top), h_top - hhlkp1, hhlk - hhlkp1)
        dh = xr.where((hhlkp1 < h_bottom) & (hhlk > h_bottom), hhlk - h_bottom, dh)

        # ... find field and dh where hfl is in interval [h_bottom, h_top]
        field_in_h_bounds = field_on_fl.where(
            (hfl >= h_bottom) & (hfl <= h_top), drop=True
        )
        dh_in_h_bounds = dh.where((hfl >= h_bottom) & (hfl <= h_top), drop=True)
        # ... compute integral by midpoint rule (apply fractional corrections for the height intervals containing h_top and h_bottom)
        #     at grid points where field_in_h_bounds is not undefined for all entries along dimension "generalVerticalLayer"
        # NOTE: The vertical dimension is lost in the reduction operation.
        # TODO: assign coordinates and attributes to rfield
        #       ensure that dh_in_h_bounds.size > 0; return everywhere undefined rfield otherwise
        rfield = xr.where(
            dh_in_h_bounds.count(dim="generalVerticalLayer") > 0,
            (field_in_h_bounds * dh_in_h_bounds)
            .fillna(0.0)
            .sum(dim="generalVerticalLayer"),
            np.nan,
        )
        if operator == "normed_integral":
            rfield /= h_top - h_bottom
    else:
        if "generalVerticalLayer" in field.coords:
            vertical_dim = "generalVerticalLayer"
        else:
            vertical_dim = "generalVertical"
        if vertical_dim not in height.coords:
            raise RuntimeError(
                "reduce_k: height is not defined for the same level type as field (required type is ",
                vertical_dim,
                ")",
            )
        field_in_h_bounds = field.where(
            (height >= h_bottom) & (height <= h_top), drop=True
        )
        heightkp1 = height.copy()
        heightkp1 = height[{vertical_dim: slice(1, None)}].assign_coords(
            {vertical_dim: height[{vertical_dim: slice(0, -1)}][vertical_dim]}
        )
        fieldkp1 = field.copy()
        fieldkp1 = field[{vertical_dim: slice(1, None)}].assign_coords(
            {vertical_dim: field[{vertical_dim: slice(0, -1)}][vertical_dim]}
        )
        gradf = (field - fieldkp1) / (height - heightkp1)
        gradfkm1 = gradf.copy()
        gradfkm1[{vertical_dim: slice(1, None)}] = gradf[
            {vertical_dim: slice(0, -1)}
        ].assign_coords(
            {vertical_dim: gradf[{vertical_dim: slice(1, None)}][vertical_dim]}
        )
        field_extrapolated_to_h_top = xr.where(
            (height > h_top) & (heightkp1 < h_top),
            field + gradf * (height - h_top),
            np.nan,
        ).dropna(vertical_dim)
        field_extrapolated_to_h_bottom = xr.where(
            (heightkp1 < h_bottom) & (height > h_bottom),
            field + gradfkm1 * (height - h_bottom),
            np.nan,
        ).dropna(vertical_dim)

        # ... compute the extremum
        if operator == "minimum":
            rfield = field_in_h_bounds.min(dim=[vertical_dim])
            if field_extrapolated_to_h_bottom.size > 0:
                rfield = xr.where(
                    field_extrapolated_to_h_bottom < rfield,
                    field_extrapolated_to_h_bottom,
                    rfield,
                )
            if field_extrapolated_to_h_top.size > 0:
                rfield = xr.where(
                    field_extrapolated_to_h_top < rfield,
                    field_extrapolated_to_h_top,
                    rfield,
                )
        else:
            rfield = field_in_h_bounds.max(dim=[vertical_dim])
            if field_extrapolated_to_h_bottom.size > 0:
                rfield = xr.where(
                    field_extrapolated_to_h_bottom > rfield,
                    field_extrapolated_to_h_bottom,
                    rfield,
                )
            if field_extrapolated_to_h_top.size > 0:
                rfield = xr.where(
                    field_extrapolated_to_h_top > rfield,
                    field_extrapolated_to_h_top,
                    rfield,
                )

    return rfield
