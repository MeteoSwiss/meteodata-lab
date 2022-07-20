"""Vertical interpolation operators."""

from ast import Pass
from re import match
import xarray as xr
import numpy as np

def interpolate_k2p(field, mode, pfield, tcp_values, tcp_units):
    """Interpolate a field from model (k) levels to pressure coordinates"""
    # Arguments
    # field: source field (xarray.DataArray)
    # mode: interpolation algorithm, one of {"lin_p", "lin_lnp", "nearest"}
    # tcp_values: target coordinate values (list)
    # tcps_units: target coordinate units (string)
    # pfield: pressure field on k levels (xarray.DataArray)
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
            if np.abs(p0 - p1) > np.abs(p0 - p2):
                ratio = 1.
            else:
                ratio = 0.

        # ... interpolate and update ftc
        ftc[{tc["typeOfLevel"]: tc_idx}] = (1. - ratio ) * f1 + ratio * f2
     

    return ftc



    


    

