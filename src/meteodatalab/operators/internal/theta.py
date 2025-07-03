"""Theta computation with fieldextra constants."""

# Third-party
import xarray as xr

# Local
from ... import metadata
from ... import physical_constants as pc


def compute_theta(p, t):
    p0 = 1.0e5
    return xr.DataArray(
        data=(p0 / p) ** pc.rdocp * t,
        attrs=metadata.override(p.metadata, shortName="PT"),
    )
