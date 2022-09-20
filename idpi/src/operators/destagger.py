"""algorithm for destaggering a field."""


def destagger(field, dim):
    """Destagger a field.

    Arguments:
    ----------
    field: xarray.DataArray
        field to destagger
    dim: str
        dimension, one of {"x", "y", "generalVertical"}

    Returns:
    --------
    dfield: xarray.DataArray
        destaggered field with dimensions in {"x","y","generalVerticalLayer"}

    """
    if dim == "x" or dim == "y":
        field_ = field
        field_[{dim: slice(1, None)}] = (
            field[{dim: slice(0, -1)}] + field[{dim: slice(1, None)}]
        ) * 0.5
        return field_
    elif dim == "generalVertical":
        field_k0_ = field[{dim: slice(0, -1)}].assign_coords(
            {dim: field[{dim: slice(0, -1)}].generalVertical}
        )

        field_k1_ = field[{dim: slice(1, None)}].assign_coords(
            {dim: field[{dim: slice(0, -1)}].generalVertical}
        )
        return ((field_k0_ + field_k1_) * 0.5).rename(
            {"generalVertical": "generalVerticalLayer"}
        )

    raise RuntimeError("Unknown dimension", dim)
