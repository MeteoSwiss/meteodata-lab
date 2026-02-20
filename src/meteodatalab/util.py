"""Util module."""

# Standard library
import dataclasses as dc
import enum
import functools
import heapq
import itertools
import logging
import typing
import warnings
from collections.abc import Callable

# Third-party
import requests
from requests.adapters import HTTPAdapter
from typing_extensions import ParamSpec
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


P = ParamSpec("P")
K = typing.TypeVar("K", bound=typing.Hashable)
T = typing.TypeVar("T")
F = Callable[P, T]


# Work around for sentinel object pending PEP 661
class Removed(enum.Enum):
    token = 0


REMOVED = Removed.token


@dc.dataclass(unsafe_hash=True, order=True)
class Entry(typing.Generic[K]):
    count: int
    item: K | Removed


class Queue(typing.Generic[K]):
    # Adapted from priority queue example in heapq documentation

    class Full(Exception):
        """Exception indicating that the queue is full."""

    def __init__(self, maxsize: int) -> None:
        self.queue: list[Entry[K]] = []
        self.finder: dict[K, Entry[K]] = {}
        self.counter = itertools.count()
        self.maxsize = maxsize
        self.size = 0

    def add_item(self, item: K) -> None:
        if item in self.finder:
            self.remove_item(item)
        elif self.size >= self.maxsize:
            raise self.Full
        count = next(self.counter)
        entry = Entry(count, item)
        self.finder[item] = entry
        heapq.heappush(self.queue, entry)
        self.size += 1

    def remove_item(self, item: K) -> None:
        entry = self.finder.pop(item)
        entry.item = REMOVED
        self.size -= 1

    def pop_item(self) -> K:
        while self.queue:
            item = heapq.heappop(self.queue).item
            if item is not REMOVED:
                del self.finder[item]
                self.size -= 1
                return item
        raise KeyError("pop from empty queue")


def memoize(key_maker: Callable[P, K], maxsize: int = 10) -> Callable[[F], F]:
    if maxsize < 1:
        raise ValueError("maxsize must be 1 or more")

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        cache: dict[K, T] = {}
        queue: Queue[K] = Queue(maxsize=maxsize)

        @functools.wraps(func)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            key = key_maker(*args, **kwargs)
            if key is not None and key in cache:
                queue.add_item(key)
                return cache[key]

            result = func(*args, **kwargs)
            if key is not None:
                cache[key] = result
                try:
                    queue.add_item(key)
                except queue.Full:
                    old_key = queue.pop_item()
                    del cache[old_key]
                    queue.add_item(key)
            return result

        return wrapped

    return decorator


def warn_deprecation(message: str) -> None:
    warnings.warn(message, DeprecationWarning, stacklevel=2)
