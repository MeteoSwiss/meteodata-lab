"""Manage GRIB metadata."""

# Standard library
import io
import typing

# Third-party
import earthkit.data as ekd  # type: ignore
from earthkit.data.writers import write  # type: ignore


def override(message: bytes, **kwargs: typing.Any) -> dict[str, typing.Any]:
    """Override GRIB metadata contained in message.

    Note that no special consideration is made for maintaining consistency when
    overriding template definition keys such as productDefinitionTemplateNumber.

    Parameters
    ----------
    message : bytes
        Byte string of the input GRIB message
    kwargs : Any
        Keyword arguments forwarded to earthkit-data GribMetadata override method

    Returns
    -------
    dict[str, Any]
        Updated message byte string along with the geography and parameter namespaces

    """
    stream = io.BytesIO(message)
    [grib_field] = ekd.from_source("stream", stream)

    out = io.BytesIO()
    md = grib_field.metadata().override(**kwargs)
    write(out, grib_field.values, md)

    return {
        "message": out.getvalue(),
        "geography": md.as_namespace("geography"),
        "parameter": md.as_namespace("parameter"),
    }
