"""Util module."""

# Standard library
import functools
import logging
from queue import Queue

# Third-party
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def init_session(logger: logging.Logger | None = None) -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=3,
        allowed_methods=["POST"],
        status_forcelist=[500],
        backoff_factor=0.25,
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))

    if logger is not None:

        def _log_errors(resp: requests.Response, *args, **kwargs):
            if not resp.ok:
                logger.error(
                    "Request to url: %s failed with status code: %d, body: %s",
                    resp.url,
                    resp.status_code,
                    resp.json(),
                )

        session.hooks["response"].append(_log_errors)

    return session


def memoize(func, maxsize=10):
    cache = {}
    queue = Queue(maxsize=maxsize)

    @functools.wraps(func)
    def wrapped(field, dst):
        key = None
        if (md5 := field.metadata.get("md5Section3", None)) is not None:
            key = md5, repr(dst)
            if key in cache:
                return cache[key]

        result = func(field, dst)
        if key is not None:
            cache[key] = result
            try:
                queue.put_nowait(key)
            except queue.Full:
                old_key = queue.get_nowait()
                del cache[old_key]
                queue.put_nowait(key)
        return result

    return wrapped
