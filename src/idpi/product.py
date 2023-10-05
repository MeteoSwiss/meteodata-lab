"""Product base classes."""

# Standard library
import dataclasses as dc
from abc import ABCMeta, abstractmethod

# Third-party
import dask


@dc.dataclass
class ProductDescriptor:
    input_fields: list[str]


class Product(metaclass=ABCMeta):
    """Base class for products."""

    def __init__(
        self,
        input_fields: list[str],
        delay_entire_product: bool = False,
    ):
        self._desc = ProductDescriptor(input_fields=input_fields)
        self._delay_entire_product = delay_entire_product

    @abstractmethod
    def _run(self, **args):
        pass

    def __call__(self, *args):
        if self._delay_entire_product:
            return dask.delayed(self._run, pure=True)(*args)
        else:
            return self._run(*args)

    @property
    def descriptor(self):
        return self._desc
