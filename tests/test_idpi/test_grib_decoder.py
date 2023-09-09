# Standard library
from unittest.mock import patch

# Third-party
import pytest

# First-party
from idpi.grib_decoder import GribReader


@patch("idpi.grib_decoder.earthkit.data.from_source")
def test_ref_param_not_found(mock_from_source):
    with pytest.raises(RuntimeError):
        mock_from_source.sel.return_value = []
        GribReader([])


@patch("idpi.grib_decoder.GribReader.load_grid_reference")
@patch("idpi.grib_decoder.earthkit.data.from_source")
def test_param_not_found(mock_load_grid_reference, mock_from_source):
    mock_from_source.sel.return_value = []

    with pytest.raises(RuntimeError):
        reader = GribReader([])
        reader.load_cosmo_data(["U", "V"])
