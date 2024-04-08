"""Get Meteoswiss model data from FDB or polytope."""

# Standard library
import logging
import os

# Third-party
import xarray as xr

# Local
from . import data_source, grib_decoder, mars

logger = logging.getLogger(__name__)


def get_from_fdb(request: mars.Request) -> dict[str, xr.DataArray]:
    """Get model data from FDB.

    Parameters
    ----------
    request : mars.Request
        Request for data defined in the mars language.

    Raises
    ------
    RuntimeError
        if the required environment variables for FDB are not set.
    ValueError
        if the request has a feature attribute.

    Returns
    -------
    dict[str, xarray.DataArray]
        Dataset containing the requested data.

    """
    keys = "FDB5_CONFIG", "FDB5_CONFIG_FILE"
    if all(key not in os.environ for key in keys):
        msg = (
            "Required environment variables for FDB are not set."
            "Define one of 'FDB5_CONFIG' or 'FDB5_CONFIG_FILE'"
        )
        logger.exception(msg)
        raise RuntimeError(msg)
    if request.feature is not None:
        msg = "FDB does not support the feature attribute."
        logger.exception(msg)
        raise ValueError(msg)
    logger.info("Getting request %s from FDB.", request)
    source = data_source.DataSource()
    return grib_decoder.load(source, request)


def get_from_polytope(request: mars.Request) -> dict[str, xr.DataArray]:
    """Get model data from Polytope.

    Parameters
    ----------
    request : mars.Request
        Request for data defined in the mars language.

    Raises
    ------
    RuntimeError
        if the required environment variables for polytope are not set.

    Returns
    -------
    dict[str, xarray.DataArray]
        Dataset containing the requested data.

    """
    keys = "POLYTOPE_ADDRESS", "POLYTOPE_USERNAME", "POLYTOPE_PASSWORD"
    if any(key not in os.environ for key in keys):
        msg = (
            "Required environment variables for polytope are not set."
            "Define 'POLYTOPE_ADDRESS', 'POLYTOPE_USERNAME' and 'POLYTOPE_PASSWORD'."
        )
        logger.exception(msg)
        raise RuntimeError(msg)
    if request.feature is not None:
        source = data_source.DataSource(polytope_collection="mchgj")
        [result] = source.retrieve(request)
        return result.to_xarray()
    else:
        collection = "mch"
    logger.info("Getting request %s from polytope collection %s", request, collection)
    source = data_source.DataSource(polytope_collection=collection)
    return grib_decoder.load(source, request)
