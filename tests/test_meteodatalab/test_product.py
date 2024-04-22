# Standard library
from unittest import mock

# Third-party
import pytest

# First-party
from idpi import data_source, product


class ProductA(product.Product):
    def __init__(self, mock_run):
        input_fields = {
            "U": product.Request("U"),
            "V": product.Request("V"),
            "T_f": product.Request("T"),  # aliased
        }
        super().__init__(input_fields=input_fields, delay_entire_product=False)
        self.mock_run = mock_run

    def _run(self, ds):
        self.mock_run(ds)


class ProductB(product.Product):
    def __init__(self, mock_run):
        input_fields = {
            "P": product.Request("P"),
            "T": product.Request("T"),
        }
        super().__init__(input_fields=input_fields, delay_entire_product=False)
        self.mock_run = mock_run

    def _run(self, ds):
        self.mock_run(ds)


@mock.patch.object(product.grib_decoder, "GribReader", autospec=True)
def test_merge(mock_reader_cls):
    m = mock.Mock()
    product_a = ProductA(m.a)
    product_b = ProductB(m.b)

    requested = []

    def store(req):
        requested.append(req)

    m.field.side_effect = store

    def load(reqs):
        return {key: m.field(value) for key, value in reqs.items()}

    mock_reader_cls.return_value = m.reader
    m.reader.load.side_effect = load

    source = data_source.DataSource()
    product.run_products([product_a, product_b], source)

    # requests have been merged
    observed = sorted(requested, key=lambda req: req["param"])
    expected = [product.Request(p)._asdict() for p in sorted("UVPT")]
    assert observed == expected

    # all necessary fields are present
    [ds_a] = m.a.call_args.args
    [ds_b] = m.b.call_args.args
    assert ds_a.keys() >= product_a.descriptor.input_fields.keys()
    assert ds_b.keys() >= product_b.descriptor.input_fields.keys()


class ProductC(product.Product):
    def __init__(self, mock_run):
        input_fields = {
            "T": product.Request("T", "pl"),
        }
        super().__init__(input_fields=input_fields, delay_entire_product=False)
        self.mock_run = mock_run

    def _run(self, ds):
        self.mock_run(ds)


def test_raises_on_conflict():
    m = mock.Mock()
    source = data_source.DataSource()
    with pytest.raises(RuntimeError):
        product.run_products([ProductA(m.a), ProductB(m.b), ProductC(m.c)], source)
