"""Vertical interpolation operators."""

# Standard library
from typing import Literal, Sequence

# Third-party
import numpy as np
import xarray as xr

# First-party
from idpi.operators.support_operators import (
    TargetCoordinates,
    TargetCoordinatesAttrs,
    init_field_with_vcoord,
)


def interpolate_k2p(
    field: xr.DataArray,
    mode: Literal["linear_in_p", "linear_in_lnp", "nearest_sfc"],
    p_field: xr.DataArray,
    p_tc_values: Sequence[float],
    p_tc_units: Literal["Pa", "hPa"],
) -> xr.DataArray:
    """Interpolate a field from model (k) levels to pressure coordinates.

    Example for vertical interpolation to isosurfaces of a target field,
    which is strictly monotonically decreasing with height.



    Parameters
    ----------
    field : xarray.DataArray
        field to interpolate (only typeOfLevel="generalVerticalLayer" is supported)
    mode : str
        interpolation algorithm, one of {"linear_in_p", "linear_in_lnp", "nearest_sfc"}
    p_field : xarray.DataArray
        pressure field on k levels in Pa
        (only typeOfLevel="generalVerticalLayer" is supported)
    p_tc_values : list of float
        pressure target coordinate values
    p_tc_units : str
        pressure target coordinate units

    Returns
    -------
    field_on_tc : xarray.DataArray
        field on target (i.e., pressure) coordinates

    """
    # TODO: check missing value consistency with GRIB2 (currently comparisons are
    #       done with np.nan)
    #       check that p_field is the pressure field, given in Pa (can only be done
    #       if attributes are consequently set)
    #       check that field and p_field are compatible (have the same
    #       dimensions and sizes)
    #       print warn message if result contains missing values

    # Initializations
    # ... supported interpolation modes
    interpolation_modes = ("linear_in_p", "linear_in_lnp", "nearest_sfc")
    if mode not in interpolation_modes:
        raise RuntimeError("interpolate_k2p: unknown mode", mode)
    # ... supported tc units and corresponding conversion factors to Pa
    p_tc_unit_conversions = dict(Pa=1.0, hPa=100.0)
    if p_tc_units not in p_tc_unit_conversions.keys():
        raise RuntimeError(
            "interpolate_k2p: unsupported value of p_tc_units", p_tc_units
        )
    # ... supported range of pressure tc values (in Pa)
    p_tc_min = 1.0
    p_tc_max = 120000.0

    # Define vertical target coordinates (tc)
    tc_factor = p_tc_unit_conversions[p_tc_units]
    tc_values = np.array(sorted(p_tc_values)) * tc_factor
    if np.any((tc_values < p_tc_min) | (tc_values > p_tc_max)):
        raise RuntimeError(
            "interpolate_k2p: target coordinate value out of range "
            f"(must be in interval [{p_tc_min}, {p_tc_max}]Pa)"
        )
    tc = TargetCoordinates(
        type_of_level="pressure",
        values=tc_values.tolist(),
        attrs=TargetCoordinatesAttrs(
            units="Pa",
            positive="down",
            standard_name="air_pressure",
            long_name="pressure",
        ),
    )

    # Check that typeOfLevel is supported and equal for both field and p_field
    if field.vcoord_type != "model_level":
        raise RuntimeError(
            "interpolate_k2p: field to interpolate must be defined on model levels"
        )
    if p_field.vcoord_type != "model_level":
        raise RuntimeError(
            "interpolate_k2p: pressure field must be defined on model levels"
        )
    # Check that dimensions are the same for field and p_field
    if field.origin_z != p_field.origin_z:
        raise RuntimeError(
            "interpolate_k2p: field and p_field must have equal vertical staggering"
        )

    # Prepare output field field_on_tc on target coordinates
    field_on_tc = init_field_with_vcoord(field.broadcast_like(p_field), tc, np.nan)

    # Interpolate
    # ... prepare interpolation
    pkm1 = p_field.shift(z=1)
    fkm1 = field.shift(z=1)

    # ... loop through tc values
    for tc_idx, p0 in enumerate(tc_values):
        # ... find the 3d field where pressure is > p0 on level k
        # and was <= p0 on level k-1
        p2 = p_field.where((p_field > p0) & (pkm1 <= p0))
        # ... extract the index k of the vertical layer at which p2 adopts its minimum
        #     (corresponds to search from top of atmosphere to bottom)
        # ... note that if the condition above is not fulfilled, minind will
        # be set to k_top
        minind = p2.fillna(p_tc_max).argmin(dim="z")
        # ... extract pressure and field at level k
        p2 = p2[{"z": minind}]
        f2 = field[{"z": minind}]
        # ... extract pressure and field at level k-1
        # ... note that f1 and p1 are both undefined, if minind equals k_top
        f1 = fkm1[{"z": minind}]
        p1 = pkm1[{"z": minind}]

        # ... compute the interpolation weights
        if mode == "linear_in_p":
            # ... note that p1 is undefined, if minind equals k_top, so ratio will
            # be undefined
            ratio = (p0 - p1) / (p2 - p1)

        if mode == "linear_in_lnp":
            # ... note that p1 is undefined, if minind equals k_top, so ratio will
            #  be undefined
            ratio = (np.log(p0) - np.log(p1)) / (np.log(p2) - np.log(p1))

        if mode == "nearest_sfc":
            # ... note that by construction, p2 is always defined;
            #     this operation sets ratio to 0 if p1 (and by construction also f1)
            #     is undefined; therefore, the interpolation formula below works
            #     correctly also in this case
            ratio = xr.where(np.abs(p0 - p1) >= np.abs(p0 - p2), 1.0, 0.0)

        # ... interpolate and update field_on_tc
        field_on_tc[{"pressure": tc_idx}] = (1.0 - ratio) * f1 + ratio * f2

    return field_on_tc


def interpolate_k2theta(
    field: xr.DataArray,
    mode: Literal["low_fold", "high_fold", "undef_fold"],
    th_field: xr.DataArray,
    th_tc_values: Sequence[float],
    th_tc_units: Literal["K", "cK"],
    h_field: xr.DataArray,
) -> xr.DataArray:
    """Interpolate a field from model levels to potential temperature coordinates.

       Example for vertical interpolation to isosurfaces of a target field
       that is no monotonic function of height.

    Parameters
    ----------
    field : xarray.DataArray
        field to interpolate (only typeOfLevel="generalVerticalLayer" is supported)
    mode : str
        interpolation algorithm, one of {"low_fold", "high_fold", "undef_fold"}
    th_field : xarray.DataArray
        potential temperature theta on k levels in K
        (only typeOfLevel="generalVerticalLayer" is supported)
    th_tc_values : list of float
        target coordinate values
    th_tc_units : str
        target coordinate units
    h_field : xarray.DataArray
        height on k levels (only typeOfLevel="generalVerticalLayer" is supported)

    Returns
    -------
    field_on_tc : xarray.DataArray
        field on target (i.e., theta) coordinates

    """
    # TODO: check missing value consistency with GRIB2
    #       (currently comparisons are done with np.nan)
    #       check that th_field is the theta field, given in K
    #       (can only be done if attributes are consequently set)
    #       check that field, th_field, and h_field are compatible
    #       print warn message if result contains missing values

    # ATTENTION: the attribute "positive" is not set for generalVerticalLayer
    #            we know that for COSMO it would be defined as positive:"down";
    #            for the time being,
    #            we explicitly use the height field on model mid layer
    #            surfaces as auxiliary field

    # Parameters
    # ... supported folding modes
    folding_modes = ("low_fold", "high_fold", "undef_fold")
    if mode not in folding_modes:
        raise RuntimeError("interpolate_k2theta: unsupported mode", mode)

    # ... supported tc units and corresponding conversion factor to K
    # (i.e. to the same unit as theta); according to GRIB2
    #     isentropic surfaces are coded in K; fieldextra codes
    #     them in cK for NetCDF (to be checked)
    th_tc_unit_conversions = dict(K=1.0, cK=0.01)
    if th_tc_units not in th_tc_unit_conversions.keys():
        raise RuntimeError(
            "interpolate_k2theta: unsupported value of th_tc_units", th_tc_units
        )
    # ... supported range of tc values (in K)
    th_tc_min = 1.0
    th_tc_max = 1000.0
    # ... tc values outside range of meaningful values of height,
    # used in tc interval search (in m amsl)
    h_min = -1000.0
    h_max = 100000.0

    # Define vertical target coordinates
    # Sorting cannot be exploited for optimizations, since theta is
    # not monotonous wrt to height tc values are stored in K
    tc_values = np.array(th_tc_values) * th_tc_unit_conversions[th_tc_units]
    if np.any((tc_values < th_tc_min) | (tc_values > th_tc_max)):
        raise RuntimeError(
            "interpolate_k2theta: target coordinate value "
            f"out of range (must be in interval [{th_tc_min}, {th_tc_max}]K)"
        )
    tc = TargetCoordinates(
        type_of_level="theta",
        values=tc_values.tolist(),
        attrs=TargetCoordinatesAttrs(
            units="K",
            positive="up",
            standard_name="air_potential_temperature",
            long_name="potential temperature",
        ),
    )

    # Check that typeOfLevel is supported and equal for field, th_field, and h_field
    if field.vcoord_type != "model_level" or field.origin_z != 0.0:
        raise RuntimeError(
            "interpolate_k2theta: field to interpolate must "
            "be defined on model_level layers"
        )
    if th_field.vcoord_type != "model_level" or th_field.origin_z != 0.0:
        raise RuntimeError(
            "interpolate_k2theta: theta field must be defined on model_level layers"
        )
    if h_field.vcoord_type != "model_level" or h_field.origin_z != 0.0:
        raise RuntimeError(
            "interpolate_k2theta: height field must be defined on model_level layers"
        )

    # Prepare output field field_on_tc on target coordinates
    field_on_tc = init_field_with_vcoord(field.broadcast_like(th_field), tc, np.nan)

    # Interpolate
    # ... prepare interpolation
    thkm1 = th_field.shift(z=1)
    fkm1 = field.shift(z=1)

    # ... loop through tc values
    for tc_idx, th0 in enumerate(tc.values):
        folding_coord_exception = xr.full_like(h_field[{"z": 0}], False)
        # ... find the height field where theta is >= th0 on level k and was <= th0
        #     on level k-1 or where theta is <= th0 on level k
        #     and was >= th0 on level k-1
        h = h_field.where(
            ((th_field >= th0) & (thkm1 <= th0)) | ((th_field <= th0) & (thkm1 >= th0))
        )
        if mode == "undef_fold":
            # ... find condition where more than one interval is found, which
            # contains the target coordinate value
            folding_coord_exception = xr.where(h.notnull(), 1.0, 0.0).sum(dim=["z"])
            folding_coord_exception = folding_coord_exception.where(
                folding_coord_exception > 1.0
            ).notnull()
        if mode in ("low_fold", "undef_fold"):
            # ... extract the index k of the smallest height at which
            # the condition is fulfilled
            tcind = h.fillna(h_max).argmin(dim="z")
        if mode == "high_fold":
            # ... extract the index k of the largest height at which the condition
            # is fulfilled
            tcind = h.fillna(h_min).argmax(dim="z")

        # ... extract theta and field at level k
        th2 = th_field[{"z": tcind}]
        f2 = field[{"z": tcind}]
        # ... extract theta and field at level k-1
        f1 = fkm1[{"z": tcind}]
        th1 = thkm1[{"z": tcind}]

        # ... compute the interpolation weights
        ratio = xr.where(np.abs(th2 - th1) > 0, (th0 - th1) / (th2 - th1), 0.0)

        # ... interpolate and update field_on_tc
        field_on_tc[{"theta": tc_idx}] = xr.where(
            folding_coord_exception, np.nan, (1.0 - ratio) * f1 + ratio * f2
        )

    return field_on_tc


def interpolate_k2any(
    field: xr.DataArray,
    mode: Literal["low_fold", "high_fold"],
    tc_field: xr.DataArray,
    tc_values: Sequence[float],
    h_field: xr.DataArray,
) -> xr.DataArray:
    """Interpolate a field from model levels to coordinates w.r.t. an arbitrary field.

    Example for vertical interpolation to isosurfaces of a target field
    that is no monotonic function of height.

    Parameters
    ----------
    field : xarray.DataArray
        field to interpolate (only typeOfLevel="generalVerticalLayer" is supported)
    mode : str
        interpolation algorithm, one of {"low_fold", "high_fold"}
    tc_field : xarray.DataArray
        target field
        (only typeOfLevel="generalVerticalLayer" is supported)
    tc_values : list of float
        target coordinate values
    h_field : xarray.DataArray
        height on k levels (only typeOfLevel="generalVerticalLayer" is supported)

    Returns
    -------
    field_on_tc : xarray.DataArray
        field on target coordinates

    """
    modes = ("low_fold", "high_fold")
    if mode not in modes:
        raise ValueError(f"Unsupported mode: {mode}")

    for f in (field, tc_field, h_field):
        if f.vcoord_type != "model_level" or f.origin_z != 0.0:
            raise ValueError("Input fields must be defined on full model levels")

    # ... tc values outside range of meaningful values of height,
    # used in tc interval search (in m amsl)
    h_min = -1000.0
    h_max = 100000.0

    tc = TargetCoordinates(
        type_of_level=tc_field.parameter["shortName"],
        values=list(tc_values),
        attrs=TargetCoordinatesAttrs(
            standard_name="",
            long_name=tc_field.parameter["name"],
            units=tc_field.parameter["units"],
            positive="up",
        ),
    )

    # Prepare output field field_on_tc on target coordinates
    field_on_tc = init_field_with_vcoord(field.broadcast_like(tc_field), tc, np.nan)

    # Interpolate
    # ... prepare interpolation
    tckm1 = tc_field.shift(z=1)
    fkm1 = field.shift(z=1)

    for tc_idx, value in enumerate(tc.values):
        # ... find the height field where target is >= value on level k and was <= value
        #     on level k-1 or where target is <= value on level k
        #     and was >= value on level k-1
        h = h_field.where(
            ((tc_field >= value) & (tckm1 <= value))
            | ((tc_field <= value) & (tckm1 >= value))
        )
        if mode == "low_fold":
            # ... extract the index k of the smallest height at which
            # the condition is fulfilled
            tcind = h.fillna(h_max).argmin(dim="z")
        if mode == "high_fold":
            # ... extract the index k of the largest height at which the condition
            # is fulfilled
            tcind = h.fillna(h_min).argmax(dim="z")

        # ... extract target and field at level k
        t2 = tc_field[{"z": tcind}]
        f2 = field[{"z": tcind}]
        # ... extract target and field at level k-1
        f1 = fkm1[{"z": tcind}]
        t1 = tckm1[{"z": tcind}]

        # ... compute the interpolation weights
        ratio = xr.where(np.abs(t2 - t1) > 0, (value - t1) / (t2 - t1), 0.0)

        # ... interpolate and update field_on_tc
        field_on_tc[{tc.type_of_level: tc_idx}] = (1.0 - ratio) * f1 + ratio * f2

    return field_on_tc
