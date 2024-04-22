"""functionality for tasking and parallel computing."""

# Third-party
import dask

# First-party
import meteodatalab.config


def delayed(fn):
    return (
        dask.delayed(fn, pure=True)
        if meteodatalab.config.get("enable_dask", False)
        else fn
    )


def compute(*delayed_objs):
    return (
        dask.compute(*delayed_objs)
        if meteodatalab.config.get("enable_dask", False)
        else delayed_objs
    )
