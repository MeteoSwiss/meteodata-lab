"""Vertical interpolation operators."""

import numpy as np
import xarray as xr


def interpolate_k2p(field, mode, pfield, tcp_values, tcp_units):
    """Interpolate a field from model (k) levels to pressure coordinates.

    Parameters
    ----------
    field : xarray.DataArray
        field to interpolate
    mode : str
        interpolation algorithm, one of {"linear_in_tcf", "linear_in_lntcf", "nearest_sfc"}
    pfield : xarray.DataArray
        pressure field on k levels in Pa
    tcp_values : list of float
        target coordinate values
    tcps_units : str
        target coordinate units

    Returns
    -------
    ftc : xarray.DataArray
        field on target coordinates

    """
    # TODO: check missing value consistency with GRIB2 (currently comparisons are done with np.nan)
    #       check that pfield is the pressure field, given in Pa
    #       check that field and pfield are compatible
    #       print warn message if result contains missing values

    # Initializations
    # ... supported interpolation modes
    interpolation_modes = ("linear_in_tcf", "linear_in_lntcf", "nearest_sfc")
    if mode not in interpolation_modes:
        raise RuntimeError("interpolate_k2p: unknown mode", mode)
    # ... supported tc units and corresponding conversion factors to Pa
    tcp_unit_conversions = dict(Pa=1.0, hPa=100.0)
    if tcp_units not in tcp_unit_conversions.keys():
        raise RuntimeError("interpolate_k2p: unsupported value of tcp_units", tcp_units)
    # ... supported range of tc values (in Pa)
    tc_min = 1.0
    tc_max = 120000.0

    # Define vertical target coordinates (tc)
    tc = dict()
    tc_values = tcp_values.copy()
    tc_values.sort(reverse=False)
    tc_factor = tcp_unit_conversions[tcp_units]
    tc["values"] = np.array(tc_values) * tc_factor
    if min(tc["values"]) < tc_min or max(tc["values"]) > tc_max:
        raise RuntimeError(
            "interpolate_k2p: target coordinate value out of range (must be in interval [",
            tc_min,
            ", ",
            tc_max,
            "]Pa)",
        )
    tc["attrs"] = {
        "units": "Pa",
        "positive": "down",
        "standard_name": "air_pressure",
        "long_name": "pressure",
    }
    tc["typeOfLevel"] = "isobaricInPa"
    tc["NV"] = 0

    # Prepare output field ftc on target coordinates
    # name
    ftc_name = field.name
    # attrs
    ftc_attrs = field.attrs.copy()
    ftc_attrs["GRIB_typeOfLevel"] = tc["typeOfLevel"]
    if ftc_attrs["GRIB_NV"] is not None:
        ftc_attrs["GRIB_NV"] = tc["NV"]
    # dims
    ftc_shape = list(
        len(field[d]) if d != "generalVerticalLayer" else len(tc["values"])
        for d in field.dims
    )
    ftc_dims = list(
        map(lambda x: x.replace("generalVerticalLayer", tc["typeOfLevel"]), field.dims)
    )
    ftc_dims = tuple(ftc_dims)
    ftc_shape = tuple(ftc_shape)
    # coords
    # ... inherit all except for the vertical coordinates
    ftc_coords = {c:v for c,v in field.coords.items() if c != 'generalVerticalLayer'}
    # ... initialize the vertical target coordinates
    ftc_coords[tc["typeOfLevel"]] = xr.IndexVariable(tc["typeOfLevel"], tc["values"], attrs=tc["attrs"])
    # data
    ftc_data = np.full(tuple(ftc_shape), np.nan, dtype=field.data.dtype)

    # Initialize the output field ftc
    ftc = xr.DataArray(
        name=ftc_name, data=ftc_data, dims=ftc_dims, coords=ftc_coords, attrs=ftc_attrs
    )

    # Interpolate
    # ... prepare interpolation
    pkm1 = pfield.copy()
    pkm1[{"generalVerticalLayer": slice(1, None)}] = pfield[
        {"generalVerticalLayer": slice(0, -1)}
    ].assign_coords(
        {
            "generalVerticalLayer": pfield[
                {"generalVerticalLayer": slice(1, None)}
            ].generalVerticalLayer
        }
    )

    pkp1 = pfield.copy()
    pkp1[{"generalVerticalLayer": slice(0, -1)}] = pfield[
        {"generalVerticalLayer": slice(1, None)}
    ].assign_coords(
        {
            "generalVerticalLayer": pfield[
                {"generalVerticalLayer": slice(0, -1)}
            ].generalVerticalLayer
        }
    )

    # ... loop through tc values
    for tc_idx, p0 in enumerate(tc["values"]):
        # ... find the 3d field where pressure is >= p0 on level k and was < p0 on level k-1
        p2 = pfield.where((pfield >= p0) & (pkm1 < p0), drop=True)
        if p2.size > 0:
            # ... extract the index k of the vertical layer at which p2 adopts its minimum
            minind = p2.fillna(tc_max).argmin(dim=["generalVerticalLayer"])
            # ... extract pressure and field at level k
            p2 = p2[{"generalVerticalLayer": minind["generalVerticalLayer"]}]
            f2 = field.where((pfield >= p0) & (pkm1 < p0), drop=True)[
                {"generalVerticalLayer": minind["generalVerticalLayer"]}
            ]
            # ... extract pressure and field at level k-1
            f1 = field.where((pfield < p0) & (pkp1 >= p0), drop=True)[
                {"generalVerticalLayer": minind["generalVerticalLayer"]}
            ]
            p1 = pfield.where((pfield < p0) & (pkp1 >= p0), drop=True)[
                {"generalVerticalLayer": minind["generalVerticalLayer"]}
            ]

            # ... compute the interpolation weights
            if mode == "linear_in_tcf":
                ratio = (p0 - p1) / (p2 - p1)

            if mode == "linear_in_lntcf":
                ratio = (np.log(p0) - np.log(p1)) / (np.log(p2) - np.log(p1))

            if mode == "nearest_sfc":
                ratio = xr.where(np.abs(p0 - p1) > np.abs(p0 - p2), 1.0, 0.0)

            # ... interpolate and update ftc
            ftc[{tc["typeOfLevel"]: tc_idx}] = (1.0 - ratio) * f1 + ratio * f2

    return ftc


def interpolate_k2theta(field, mode, thfield, tcth_values, tcth_units, hfield):
    """Interpolate a field from model (k) levels to potential temperature (theta) coordinates.

    Parameters
    ----------
    field : xarray.DataArray
        field to interpolate
    mode : str
        interpolation algorithm, one of {"low_fold", "high_fold","undef_fold"}
    thfield : xarray.DataArray
        potential temperature theta on k levels in K
    tcth_values : list of float
        target coordinate values
    tcth_units : str
        target coordinate units
    hfield : xarray.DataArray
        height on k levels

    Returns
    -------
    ftc : xarray.DataArray
        field on target coordinates

    """
    # TODO: check missing value consistency with GRIB2 (currently comparisons are done with np.nan)
    #       check that thfield is the theta field, given in K
    #       check that field, thfield, and hfield are compatible
    #       print warn message if result contains missing values

    # ATTENTION: the attribute "positive" is not set for generalVerticalLayer
    #            we know that for COSMO it would be defined as positive:"down"; for the time being,
    #            we explicitly use the height field on model mid layer surfaces as auxiliary field

    # Parameters
    # ... supported folding modes
    folding_modes = ("low_fold", "high_fold", "undef_fold")
    if mode not in folding_modes:
        raise RuntimeError("interpolate_k2theta: unsupported mode", mode)

    # ... supported tc units and corresponding conversion factor to K (i.e. to the same unit as theta); according to GRIB2
    #     isentropic surfaces are coded in K; fieldextra codes them in cK for NetCDF (to be checked)
    tcth_unit_conversions = dict(K=1.0, cK=0.01)
    if tcth_units not in tcth_unit_conversions.keys():
        raise RuntimeError(
            "interpolate_k2theta: unsupported value of tcth_units", tcth_units
        )
    # ... supported range of tc values (in K)
    tc_min = 1.0
    tc_max = 1000.0
    # ... tc values outside range of meaningful values of height, used in tc interval search (in m amsl)
    h_min = -1000.0
    h_max = 100000.0

    # Define vertical target coordinates
    tc = dict()
    tc_values = tcth_values.copy()
    tc_values.sort(
        reverse=False
    )  # Sorting cannot be exploited for optimizations, since theta is not monotonous wrt to height
    # tc values are stored in K
    tc["values"] = np.array(tcth_values) * tcth_unit_conversions[tcth_units]
    if min(tc["values"]) < tc_min or max(tc["values"]) > tc_max:
        raise RuntimeError(
            "interpolate_k2theta: target coordinate value out of range (must be in interval [",
            tc_min,
            ", ",
            tc_max,
            "]K)",
        )
    tc["attrs"] = {
        "units": "K",
        "positive": "up",
        "standard_name": "air_potential_temperature",
        "long_name": "potential temperature",
    }
    tc["typeOfLevel"] = "theta"  # not yet properly defined in eccodes
    tc["NV"] = 0

    # Prepare output field ftc on tc
    # name
    ftc_name = field.name
    # attrs
    ftc_attrs = field.attrs.copy()
    ftc_attrs["GRIB_typeOfLevel"] = tc["typeOfLevel"]
    if ftc_attrs["GRIB_NV"] is not None:
        ftc_attrs["GRIB_NV"] = tc["NV"]
    # dims
    ftc_shape = list(
        len(field[d]) if d != "generalVerticalLayer" else len(tc["values"])
        for d in field.dims
    )
    ftc_dims = tuple(
        map(lambda x: x.replace("generalVerticalLayer", tc["typeOfLevel"]), field.dims)
    )
    ftc_shape = tuple(ftc_shape)
    # coords
    # ... inherit all except for the vertical coordinates
    ftc_coords = {c:v for c,v in field.coords.items() if c != 'generalVerticalLayer'}
    
    # ... initialize the vertical target coordinates
    ftcth_coords = xr.IndexVariable(tc["typeOfLevel"], tc["values"], attrs=tc["attrs"])
    ftc_coords[ftcth_coords.name] = ftcth_coords
    # data, filled with missing values
    ftc_data = np.full(tuple(ftc_shape), np.nan, dtype=field.data.dtype)

    # Initialize the output field ftc
    ftc = xr.DataArray(
        name=ftc_name, data=ftc_data, dims=ftc_dims, coords=ftc_coords, attrs=ftc_attrs
    )

    # Interpolate
    # ... prepare interpolation
    thkm1 = thfield.copy()
    thkm1[{"generalVerticalLayer": slice(1, None)}] = thfield[
        {"generalVerticalLayer": slice(0, -1)}
    ].assign_coords(
        {
            "generalVerticalLayer": thfield[
                {"generalVerticalLayer": slice(1, None)}
            ].generalVerticalLayer
        }
    )

    thkp1 = thfield.copy()
    thkp1[{"generalVerticalLayer": slice(0, -1)}] = thfield[
        {"generalVerticalLayer": slice(1, None)}
    ].assign_coords(
        {
            "generalVerticalLayer": thfield[
                {"generalVerticalLayer": slice(0, -1)}
            ].generalVerticalLayer
        }
    )

    # ... loop through tc values
    for tc_idx, th0 in enumerate(tc["values"]):
        folding_coord_exception = xr.full_like(
            hfield[{"generalVerticalLayer": 0}], False
        )
        # ... find the height field where theta is >= th0 on level k and was <= th0 on level k-1
        #     or where theta is <= th0 on level k and was >= th0 on level k-1
        h = hfield.where(
            ((thfield >= th0) & (thkm1 <= th0)) | ((thfield <= th0) & (thkm1 >= th0)),
            drop=True,
        )
        if h.size > 0:
            if mode == "undef_fold":
                # ... find condition where more than one interval is found, which contains the target coordinate value
                folding_coord_exception = xr.where(h.notnull(), 1.0, 0.0).sum(
                    dim=["generalVerticalLayer"]
                )
                folding_coord_exception = folding_coord_exception.where(
                    folding_coord_exception > 1.0
                ).notnull()
            if mode in ("low_fold", "undef_fold"):
                # ... extract the index k of the smallest height at which the condition is fulfilled
                tcind = h.fillna(h_max).argmin(dim=["generalVerticalLayer"])
            if mode == "high_fold":
                # ... extract the index k of the largest height at which the condition is fulfilled
                tcind = h.fillna(h_min).argmax(dim=["generalVerticalLayer"])

            # ... extract theta and field at level k
            th2 = thfield.where(
                ((thfield >= th0) & (thkm1 <= th0))
                | ((thfield <= th0) & (thkm1 >= th0)),
                drop=True,
            )[{"generalVerticalLayer": tcind["generalVerticalLayer"]}]
            f2 = field.where(
                ((thfield >= th0) & (thkm1 <= th0))
                | ((thfield <= th0) & (thkm1 >= th0)),
                drop=True,
            )[{"generalVerticalLayer": tcind["generalVerticalLayer"]}]
            # ... extract theta and field at level k-1
            f1 = field.where(
                ((thfield <= th0) & (thkp1 >= th0))
                | ((thfield >= th0) & (thkp1 <= th0)),
                drop=True,
            )[{"generalVerticalLayer": tcind["generalVerticalLayer"]}]
            th1 = thfield.where(
                ((thfield <= th0) & (thkp1 >= th0))
                | ((thfield >= th0) & (thkp1 <= th0)),
                drop=True,
            )[{"generalVerticalLayer": tcind["generalVerticalLayer"]}]

            # ... compute the interpolation weights
            ratio = xr.where(np.abs(th2 - th1) > 0, (th0 - th1) / (th2 - th1), 0.0)

            # ... interpolate and update ftc
            ftc[{tc["typeOfLevel"]: tc_idx}] = xr.where(
                folding_coord_exception, np.nan, (1.0 - ratio) * f1 + ratio * f2
            )

    return ftc
