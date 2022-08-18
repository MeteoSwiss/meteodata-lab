"""algorithm for destaggering a field."""


def destagger(field, dim):
    """Destagger a field.

    Arguments:
    ----------
    field: xarray.DataArray
        field to destagger
    dim: str
        target dimension, one of {"x", "y", "generalVerticalLayer"}
        coord attribute will have the specified value after destaggering

    Returns:
    --------
    dfield: xarray.DataArray
        destaggered field

    """
    if dim == "x" or dim == "y":
        field_ = field
        field_[{dim: slice(1, None)}] = (
            field[{dim: slice(0, -1)}] + field[{dim: slice(1, None)}]
        ) * 0.5
        return field_
    elif dim == "generalVerticalLayer":
        # TODO: check that the vertical dimension of field is of type generalVerticalLayer
        #       correct wrong usage of generalVerticalLayer to generalVertical consistently
        #       with grib_decoder.py
        field_k0_ = field[{dim: slice(0, -1)}].assign_coords(
            {dim: field[{dim: slice(0, -1)}].generalVerticalLayer}
        )

        field_k1_ = field[{dim: slice(1, None)}].assign_coords(
            {dim: field[{dim: slice(0, -1)}].generalVerticalLayer}
        )
        return (field_k0_ + field_k1_) * 0.5

    raise RuntimeError("Unknown dimension", dim)
