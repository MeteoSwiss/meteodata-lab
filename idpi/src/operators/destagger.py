"""algorithm for destaggering a field."""


def destagger(field, dim):
    """Destagger a field."""
    if dim == "x" or dim == "y":
        field_ = field
        field_[{dim: slice(1, None)}] = (
            field[{dim: slice(0, -1)}] + field[{dim: slice(1, None)}]
        ) * 0.5
        return field_
    elif dim == "generalVerticalLayer":
        hhl_k0 = field[{dim: slice(0, -1)}].assign_coords(
            {dim: field[{dim: slice(0, -1)}].generalVerticalLayer}
        )

        hhl_k1 = field[{dim: slice(1, None)}].assign_coords(
            {dim: field[{dim: slice(0, -1)}].generalVerticalLayer}
        )
        return (hhl_k0 + hhl_k1) * 0.5

    raise RuntimeError("Unknown dimension", dim)
