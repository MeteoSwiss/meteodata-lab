"""functionality for tasking and parallel computing."""

# Third-party
import dask

# First-party
import meteodatalab.config

# Local
from .util import warn_deprecation


def delayed(fn):
    warn_deprecation("tasking module will be removed in version 0.6")
    return (
        dask.delayed(fn, pure=True)
        if meteodatalab.config.get("enable_dask", False)
        else fn
    )


def compute(*delayed_objs):
    warn_deprecation("tasking module will be removed in version 0.6")
    return (
        dask.compute(*delayed_objs)
        if meteodatalab.config.get("enable_dask", False)
        else delayed_objs
    )
