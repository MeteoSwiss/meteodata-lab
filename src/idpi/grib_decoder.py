"""Decoder for grib data."""
# Third-party
import cfgrib  # type: ignore


def load_data(outds, fields, datafile, chunk_size=10):
    chunk_arg = {}
    if chunk_size:
        chunk_arg = {"chunks": {"generalVerticalLayer": chunk_size}}

    # Note: dataset assignment is based on typeOfLevel in cfgrib
    dss = cfgrib.open_datasets(
        datafile,
        backend_kwargs={"read_keys": ["typeOfLevel", "gridType"]},
        encode_cf=("time", "geography", "vertical"),
        **chunk_arg,
    )
    for ds in dss:
        for field in fields:
            if field in ds:
                outds[field] = ds[field]
                if field == "HHL":
                    outds[field] = outds[field].interpolate_na(dim="generalVertical")

    if any(field not in outds for field in fields):
        raise RuntimeError("Not all fields found in datafile", fields)
