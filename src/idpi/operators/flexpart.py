"""Flexpart operators."""

# Standard library
import io

# Third-party
import cfgrib  # type: ignore
import numpy as np
import xarray as xr
import yaml

# First-party
from idpi.operators.omega_slope import omega_slope
from idpi.operators.time_operators import time_rate


class ifs_data_loader:
    """Class for loading data from ifs and convert conventions to COSMO."""

    def __init__(self, field_mapping_file: io.TextIOWrapper):
        """Initialize the data loader.

        Args:
            field_mapping_file: mappings between IFS and internal var names

        """
        self._field_map = yaml.safe_load(field_mapping_file)

    def open_ifs_to_cosmo(
        self, datafile: str, fields: list[str], load_pv: bool = False
    ):
        """Load IFS data in a dictionary where the keys are COSMO variables.

        IFS and COSMO use different shortNames. IFS are lower case,
        while COSMO are upper case. In order to have a more homogeneous data management
        in idpi and operators, we convert the keys from IFS to COSMO conventions.
        Additionally it applies unit conversions from IFS to COSMO.
        """
        ds = {}

        read_keys = [
            "edition",
            "productDefinitionTemplateNumber",
            "uvRelativeToGrid",
            "resolutionAndComponentFlags",
            "section4Length",
            "PVPresent",
            "productionStatusOfProcessedData",
        ]
        if load_pv:
            read_keys.append("pv")

        ifs_multi_ds = cfgrib.open_datasets(
            datafile,
            backend_kwargs={
                "read_keys": read_keys,
                "indexpath": "",
            },
            encode_cf=("time", "geography", "vertical"),
        )

        for f in fields:
            ds[f] = self._get_da(self._field_map[f]["ifs"]["name"], ifs_multi_ds)
            if ds[f].GRIB_edition == 1:
                # Somehow grib1 loads a perturbationNumber=0 which sets a 'number'
                # coordinate. That will force in cfgrib setting the
                # productDefinitionTemplateNumber to 1
                # https://github.com/ecmwf/cfgrib/blob/27071067bcdd7505b1abbcb2cea282cf23b36598/cfgrib/xarray_to_grib.py#L123
                ds[f] = ds[f].drop_vars("number")

            if "cosmo" in self._field_map[f]:
                ufact = self._field_map[f]["cosmo"].get("unit_factor")

                if ufact:
                    ds[f] *= ufact

        return ds

    def _get_da(self, field, dss):
        for ds in dss:
            if field in ds:
                return ds[field]


def load_flexpart_data(fields, loader, datafile):
    fields_ = list(fields)
    fields_.remove("U")
    ds = loader.open_ifs_to_cosmo(datafile, fields_)
    ds.update(loader.open_ifs_to_cosmo(datafile, ["U"], load_pv=True))
    append_pv_raw(ds)

    ds["U"] = ds["U"].sel(hybrid=slice(40, 137))
    ds["V"] = ds["V"].sel(hybrid=slice(40, 137))
    ds["ETADOT"] = ds["ETADOT"].sel(hybrid=slice(1, 137))
    ds["T"] = ds["T"].sel(hybrid=slice(40, 137))
    ds["QV"] = ds["QV"].sel(hybrid=slice(40, 137))

    return ds


def append_pv_raw(ds):
    """Compute ak, bk (weights that define the vertical coordinate) from pv."""
    NV = ds["U"].GRIB_NV

    ds["ak"] = xr.DataArray(
        ds["U"].GRIB_pv[0 : int(NV / 2)], dims=("hybrid_pv")
    ).assign_coords(
        {
            "hybrid_pv": np.append(
                ds["ETADOT"].hybrid.data, [len(ds["ETADOT"].hybrid) + 1]
            ),
            "time": ds["ETADOT"].time,
            "step": ds["ETADOT"].step,
        }
    )
    ds["bk"] = xr.DataArray(
        ds["U"].GRIB_pv[int(NV / 2) : NV], dims=("hybrid_pv")
    ).assign_coords(
        {
            "hybrid_pv": np.append(
                ds["ETADOT"].hybrid.data, [len(ds["ETADOT"].hybrid) + 1]
            ),
            "time": ds["ETADOT"].time,
            "step": ds["ETADOT"].step,
        }
    )


def fflexpart(ds, istep):
    ds_out = {}
    for field in (
        "U",
        "V",
        "T",
        "QV",
        "PS",
        "U_10M",
        "V_10M",
        "T_2M",
        "TD_2M",
        "CLCT",
        "W_SNOW",
    ):
        ds_out[field] = ds[field].isel(step=istep).expand_dims(dim="step")

    ds_out["TOT_CON"] = time_rate(
        ds["TOT_CON"].isel(step=slice(istep - 1, istep + 1)), np.timedelta64(1, "h")
    )
    ds_out["TOT_CON"].attrs = ds["TOT_CON"].attrs
    ds_out["TOT_GSP"] = time_rate(
        ds["TOT_GSP"].isel(step=slice(istep - 1, istep + 1)), np.timedelta64(1, "h")
    )

    ds_out["TOT_GSP"].attrs = ds["TOT_GSP"].attrs
    ds_out["ASOB_S"] = time_rate(
        ds["ASOB_S"].isel(step=slice(istep - 1, istep + 1)), np.timedelta64(1, "s")
    )
    ds_out["ASOB_S"].attrs = ds["ASOB_S"].attrs
    ds_out["ASHFL_S"] = time_rate(
        ds["ASHFL_S"].isel(step=slice(istep - 1, istep + 1)), np.timedelta64(1, "s")
    )
    ds_out["ASHFL_S"].attrs = ds["ASHFL_S"].attrs
    ds_out["EWSS"] = time_rate(
        ds["EWSS"].isel(step=slice(istep - 1, istep + 1)), np.timedelta64(1, "s")
    )

    ds_out["EWSS"].attrs = ds["EWSS"].attrs

    ds_out["OMEGA"] = omega_slope(
        ds["PS"].isel(step=istep),
        ds["ETADOT"].isel(step=istep),
        ds["ak"].isel(step=istep),
        ds["bk"].isel(step=istep),
    ).isel(hybrid=slice(39, 137))

    return ds_out
