"""Vertical interpolation operators."""

from ast import Pass
from re import match
import xarray as xr
import numpy as np

def interpolate_k2p(field, mode, pfield, tcp_values, tcp_units):
    """Interpolate a field from model (k) levels to pressure coordinates"""
    # Arguments
    # field: source field (xarray.DataArray)
    # mode: interpolation algorithm, one of {"linear_in_tcf", "linear_in_lntcf", "nearest_sfc"}
    # tcp_values: target coordinate values (list)
    # tcps_units: target coordinate units (string)
    # pfield: pressure field on k levels in Pa (xarray.DataArray)
    #
    # Result
    # ftc: target field (xarray.DataArray)
    # xarray.DataArray key properties:
    #   name (str)
    #   data (numpy.ndarray)
    #   dims (tuple of str)
    #   coords (dict-like container of arrays (ccordinates))
    #   attrs (dict to hold arbitrary metadata)

    # TODO: check missing value consistency with GRIB2 (currently comparisons are done with np.nan)
    #       check that pfield is the pressure field, given in Pa
    #       check that field and pfield are compatible
    #       handle the case that the tc pressure values are out of range of pfield

    # Parameters
    # ... supported interpolation modes
    interpolation_modes = dict(linear_in_tcf=1, linear_in_lntcf=2, nearest_sfc=3)
    # ... supported tc units and corresponding conversion factors
    tcp_unit_conversions = dict(Pa=1., hPa=100.)
    # ... tc value beyond upper bound for meaningful values of pressure, used in tc interval search (in Pa)
    tc_max = 200000.

    # Define vertical target coordinates
    tc = dict()
    tc_data = tcp_values.copy()
    tc_data.sort(reverse=False)
    tc["data"] = np.array(tc_data)
    tc_factor = tcp_unit_conversions.get(tcp_units)
    if tc_factor is not None:
        tc["data"] *= tc_factor
    else:
        raise RuntimeError("interpolate_k2p: unknown pressure coordinate units", tcp_units)    
    tc["attrs"] = {"units": "Pa",
                   "positive": "down",
                   "standard_name": "air_pressure",
                   "long_name": "pressure"
                  }
    tc["typeOfLevel"] = "isobaricInPa"
    tc["NV"] = 0
    tc["mode"] = interpolation_modes.get(mode)
    if tc["mode"] is None:
        raise RuntimeError("interpolate_k2p: unknown mode", mode)

    # Prepare output field ftc on tc
    # name
    ftc_name = field.name
    # attrs
    ftc_attrs = field.attrs.copy()
    ftc_attrs["GRIB_typeOfLevel"] = tc["typeOfLevel"]
    if ftc_attrs["GRIB_NV"] is not None:
        ftc_attrs["GRIB_NV"] = tc["NV"]
    # dims
    ftc_dims = []
    ftc_dim_lens = []
    for d in field.dims:
        if d != "generalVerticalLayer":
            ftc_dims.append(d)
            ftc_dim_lens.append(len(field[d]))
        else:
            ftc_dims.append(tc["typeOfLevel"])
            ftc_dim_lens.append(len(tc["data"]))
    ftc_dims = tuple(ftc_dims)
    ftc_dim_lens = tuple(ftc_dim_lens)
    # coords
    # ... inherit all except for the vertical coordinates
    ftc_coords = {}
    for c in field.coords:
        if c != "generalVerticalLayer":
            ftc_coords[c] = field.coords[c]
    # ... initialize the vertical target coordinates
    ftcp_coords = xr.IndexVariable(tc["typeOfLevel"], tc["data"], attrs=tc["attrs"])
    ftc_coords[ftcp_coords.name] = ftcp_coords
    # data
    ftc_data = np.ndarray( tuple(ftc_dim_lens), dtype=float )
    # ... fill with missing values (alternatively, use field.attrs["GRIB_missingValue"])
    ftc_data.fill(np.nan)

    # Initialize the output field ftc
    ftc = xr.DataArray(name=ftc_name, data=ftc_data, dims=ftc_dims, coords=ftc_coords, attrs=ftc_attrs)

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
    for tc_idx in range(len(tc["data"])):
        p0 = tc["data"][tc_idx]
        # ... find the 3d field where pressure is >= p0 on level k and was < p0 on level k-1
        p2 = pfield.where((pfield >= p0) & (pkm1 < p0), drop=True)
        if p2.size > 0:
            # ... extract the index k of the vertical layer at which p2 adopts its minimum
            minind = p2.fillna(tc_max).argmin(dim=["generalVerticalLayer"])
            # ... extract pressure and field at level k
            p2 = p2[{"generalVerticalLayer": minind["generalVerticalLayer"]}]
            f2 = field.where((pfield >= p0) & (pkm1 < p0), drop=True)[{"generalVerticalLayer": minind["generalVerticalLayer"]}]
            # ... extract pressure and field at level k-1
            f1 = field.where((pfield < p0) & (pkp1 >= p0), drop=True)[{"generalVerticalLayer": minind["generalVerticalLayer"]}]
            p1 = pfield.where((pfield < p0) & (pkp1 >= p0), drop=True)[{"generalVerticalLayer": minind["generalVerticalLayer"]}]

            # ... compute the interpolation weights
            if tc["mode"] == interpolation_modes["linear_in_tcf"]:
                ratio = (p0 - p1) / (p2 - p1)

            if tc["mode"] == interpolation_modes["linear_in_lntcf"]:
                ratio = (np.log(p0) - np.log(p1)) / (np.log(p2) - np.log(p1))

            if tc["mode"] == interpolation_modes["nearest_sfc"]:
                ratio = xr.where(np.abs(p0 - p1) > np.abs(p0 - p2), 1., 0.)

            # ... interpolate and update ftc
            ftc[{tc["typeOfLevel"]: tc_idx}] = (1. - ratio ) * f1 + ratio * f2
     
    return ftc


def interpolate_k2theta(field, mode, thfield, tcth_values, tcth_units, hfield):
    """Interpolate a field from model (k) levels to potential temperature (theta) coordinates"""
    # Arguments
    # field: source field (xarray.DataArray)
    # mode: interpolation algorithm, one of {"low_fold", "high_fold","undef_fold"}
    # thfield: potential temperature theta on k levels in K (xarray.DataArray)
    # tcth_values: target coordinate values (list)
    # tcth_units: target coordinate units (string)
    # hfield: height on k levels (xarray.DataArray)
    #
    # Result
    # ftc: target field (xarray.DataArray)
    # xarray.DataArray key properties:
    #   name (str)
    #   data (numpy.ndarray)
    #   dims (tuple of str)
    #   coords (dict-like container of arrays (ccordinates))
    #   attrs (dict to hold arbitrary metadata)

    # TODO: check missing value consistency with GRIB2 (currently comparisons are done with np.nan)
    #       check that thfield is the theta field, given in K
    #       check that field, thfield, and hfield are compatible
    #       print warn message if result contains missing values

    # ATTENTION: the attribute "positive" is not set for generalVerticalLayer
    #            we know that for COSMO it would be defined as positive:"down"; for the time being,
    #            we explicitly use the height field, defined on model mid layer surfaces as auxiliary field

    # Parameters
    # ... supported folding modes
    folding_modes = dict(low_fold=1, high_fold=2, undef_fold=3)
    # ... supported tc units and corresponding conversion factor to K (i.e. to the same unit as theta); according to GRIB2 
    #     isentropic surfaces are coded in K; fieldextra codes them in cK for NetCDF (to be checked)
    tcth_unit_conversions = dict(K=1., cK=100.)
    # ... tc value below and beyond upper bound for meaningful values of height, used in tc interval search (in m amsl)
    h_min = -1000.
    h_max = 100000.

    # Define vertical target coordinates
    tc = dict()
    tc_data = tcth_values.copy()
    tc_data.sort(reverse=False) # Sorting cannot be exploited for optimizations, since theta is not monotonous wrt to height
    # tc data have to be stored in cK
    tc["data"] = np.array(tc_data)
    tc_factor = tcth_unit_conversions.get(tcth_units)
    if tc_factor is not None:
        tc["data"] *= tc_factor
    else:
        raise RuntimeError("interpolate_k2theta: unknown theta coordinate units", tcth_units)    
    tc["attrs"] = {"units": "K",
                   "positive": "up",
                   "standard_name": "air_potential_temperature",
                   "long_name": "potential temperature"
                  }
    tc["typeOfLevel"] = "theta" # not yet properly defined in eccodes
    tc["NV"] = 0
    tc["mode"] = folding_modes.get(mode)
    if tc["mode"] is None:
        raise RuntimeError("interpolate_k2theta: unknown mode", mode)

    # Prepare output field ftc on tc
    # name
    ftc_name = field.name
    # attrs
    ftc_attrs = field.attrs.copy()
    ftc_attrs["GRIB_typeOfLevel"] = tc["typeOfLevel"]
    if ftc_attrs["GRIB_NV"] is not None:
        ftc_attrs["GRIB_NV"] = tc["NV"]
    # dims
    ftc_dims = []
    ftc_dim_lens = []
    for d in field.dims:
        if d != "generalVerticalLayer":
            ftc_dims.append(d)
            ftc_dim_lens.append(len(field[d]))
        else:
            ftc_dims.append(tc["typeOfLevel"])
            ftc_dim_lens.append(len(tc["data"]))
    ftc_dims = tuple(ftc_dims)
    ftc_dim_lens = tuple(ftc_dim_lens)
    # coords
    # ... inherit all except for the vertical coordinates
    ftc_coords = {}
    for c in field.coords:
        if c != "generalVerticalLayer":
            ftc_coords[c] = field.coords[c]
    # ... initialize the vertical target coordinates
    ftcth_coords = xr.IndexVariable(tc["typeOfLevel"], tc["data"], attrs=tc["attrs"])
    ftc_coords[ftcth_coords.name] = ftcth_coords
    # data
    ftc_data = np.ndarray( tuple(ftc_dim_lens), dtype=float )
    # ... fill with missing values (alternatively, use field.attrs["GRIB_missingValue"])
    ftc_data.fill(np.nan)

    # Initialize the output field ftc
    ftc = xr.DataArray(name=ftc_name, data=ftc_data, dims=ftc_dims, coords=ftc_coords, attrs=ftc_attrs)

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

    # ... loop through tc values (downward search)
    for tc_idx in range(len(tc["data"])):
        th0 = tc["data"][tc_idx]
        folding_coord_exception = xr.full_like(hfield[{"generalVerticalLayer": 0}], False)
        # ... find the height field where theta is >= th0 on level k and was <= th0 on level k-1
        #     or where theta is <= th0 on level k and was >= th0 on level k-1
        h = hfield.where(((thfield >= th0) & (thkm1 <= th0)) | ((thfield <= th0) & (thkm1 >= th0)), drop=True)
        if h.size > 0:
            if tc["mode"] == folding_modes["undef_fold"]:
                # ... find condition where more than one interval is found, which contains the target coordinate value
                folding_coord_exception = xr.where(h.notnull(), 1., 0.).sum(dim=["generalVerticalLayer"])
                folding_coord_exception = folding_coord_exception.where(folding_coord_exception >1.).notnull()
            if tc["mode"] in (folding_modes["low_fold"], folding_modes["undef_fold"]):
                # ... extract the index k of the smallest height at which the condition is fulfilled
                tcind = h.fillna(h_max).argmin(dim=["generalVerticalLayer"])
            if tc["mode"] == folding_modes["high_fold"]:
                # ... extract the index k of the largest height at which the condition is fulfilled
                tcind = h.fillna(h_min).argmax(dim=["generalVerticalLayer"])

            # ... extract theta and field at level k
            th2 = thfield.where(((thfield >= th0) & (thkm1 <= th0)) | ((thfield <= th0) & (thkm1 >= th0)), drop=True)[{"generalVerticalLayer": tcind["generalVerticalLayer"]}]
            f2 = field.where(((thfield >= th0) & (thkm1 <= th0)) | ((thfield <= th0) & (thkm1 >= th0)), drop=True)[{"generalVerticalLayer": tcind["generalVerticalLayer"]}]
            # ... extract theta and field at level k-1
            f1 = field.where(((thfield <= th0) & (thkp1 >= th0)) | ((thfield >= th0) & (thkp1 <= th0)), drop=True)[{"generalVerticalLayer": tcind["generalVerticalLayer"]}]
            th1 = thfield.where(((thfield <= th0) & (thkp1 >= th0)) | ((thfield >= th0) & (thkp1 <= th0)), drop=True)[{"generalVerticalLayer": tcind["generalVerticalLayer"]}]

            # ... compute the interpolation weights
            ratio = xr.where(np.abs(th2 - th1) > 0, (th0 - th1) / (th2 - th1), 0.)

            # ... interpolate and update ftc
            ftc[{tc["typeOfLevel"]: tc_idx}] = xr.where(folding_coord_exception, np.nan, (1. - ratio ) * f1 + ratio * f2)     

    return ftc



    


    

