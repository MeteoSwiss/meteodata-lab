"""Util module."""

# Standard library
import logging

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
