"""global configuration for idpi."""

# Standard library
from contextlib import contextmanager
from typing import Any, Literal

config: dict = {}


@contextmanager
def set_values(config: dict = config, **kwargs):
    """Temporarily set configuration values within a context manager.

    Parameters
    ----------
    config : dict, optional
        dictionary object use to hold the configuration.
        Default will use the config object in this module
    **kwargs :
        the configuration key-value pairs to set.

    """
    record: list[tuple[Literal["insert", "replace"], str, Any]] = []

    for key, value in kwargs.items():
        if key in config:
            record.append(("replace", key, config[key]))
        else:
            record.append(("insert", key, None))

        config[key] = value

    try:
        yield config
    finally:
        for op, key, value in reversed(record):
            d = config
            if op == "replace":
                d[key] = value
            else:  # insert
                d.pop(key, None)


def get(
    key: str,
    default: Any = None,
    config: dict = config,
) -> Any:
    """Get values from global config.

    Parameters
    ----------
    key: str
        specifies the name of the key for which the value is requested
    default: Any
        default value to be returned in case the key does not exist in config
    config: dict, optional
        config object holding the mapping. Default value is the global config

    """
    return config.get(key, default)
