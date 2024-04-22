"""Product base classes."""

# Standard library
import dataclasses as dc
from abc import ABCMeta, abstractmethod
from collections import Counter
from typing import NamedTuple

# Local
from . import data_source, grib_decoder, tasking


class Request(NamedTuple):
    param: str
    levtype: str = "ml"
    levelist: tuple[int, ...] | None = None


@dc.dataclass
class ProductDescriptor:
    input_fields: dict[str, Request]


class Product(metaclass=ABCMeta):
    """Base class for products."""

    def __init__(
        self,
        input_fields: dict[str, Request],
        delay_entire_product: bool = False,
    ):
        self._desc = ProductDescriptor(input_fields=input_fields)
        self._delay_entire_product = delay_entire_product

    @abstractmethod
    def _run(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        if self._delay_entire_product:
            return tasking.delayed(self._run)(*args, **kwargs)
        else:
            return self._run(*args, **kwargs)

    @property
    def descriptor(self):
        return self._desc


def _merge_requests(
    products: list[Product],
) -> tuple[dict[str, Request], dict[str, list[str]]]:
    """Deduplicate field requests for a collection of products.

    Raises RuntimeError if there are conflicts meaning that there
    different requests assigned to the same name.

    Returns the merged mapping of names to requests and name aliases.
    The alias is needed because a product will expect to find a requested
    field under the name that was attached to the request.
    """
    req_labels: dict[Request, set[str]] = {}
    for product in products:
        for name, req in product.descriptor.input_fields.items():
            name_set = req_labels.setdefault(req, set())
            name_set.add(name)

    # check for any conflicts in the names
    cnt = Counter(name for names in req_labels.values() for name in names)
    conflicts = [name for name, count in cnt.items() if count > 1]
    if conflicts:
        raise RuntimeError(f"These names are involved in conflicts: {conflicts}")

    result: dict[str, Request] = {}
    aliases: dict[str, list[str]] = {}
    for req, names in req_labels.items():
        name, *alias = names
        result[name] = req
        aliases[name] = alias

    return result, aliases


def run_products(
    products: list[Product],
    source: data_source.DataSource,
    ref_param: Request = Request("HHL"),
):
    """Run multiple products.

    Parameters
    ----------
    products : list[Product]
        List of products to run.
    source : DataSource
        Data source from which to request the fields.
    ref_param : Request, optional
        Reference parameter to determine the origin of the grid. Defaults to HHL.

    Raises
    ------
    RuntimeError
        if a single name is mapped to different input field requests.

    Returns
    -------
    tuple[Any, ...]
        Returns the collection of results.

    """
    reqs, aliases = _merge_requests(products)

    reader = grib_decoder.GribReader(source, ref_param=ref_param._asdict())
    ds = reader.load({key: req._asdict() for key, req in reqs.items()})
    for name, alias in aliases.items():
        ds.update({a: ds[name] for a in alias})

    results = [product(ds) for product in products]

    return tasking.compute(*results)
