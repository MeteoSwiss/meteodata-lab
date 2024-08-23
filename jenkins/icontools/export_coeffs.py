# Standard library
import dataclasses as dc
from pathlib import Path

# Third-party
import pyremap.iconremap as ir
import pyremap.regular_grid as rg
import xarray as xr
import yaml
import click

DEFAULTS = {
    "models": "icon-ch1-eps,icon-ch2-eps",
    "dst_grids": "rotlatlon,geolatlon",
    "grid_config_path": Path(__file__).parent / "grid_config.yaml",
}
GRID_DIR = Path("/scratch/mch/jenkins/icon/pool/data/ICON/mch/grids")
INPUT_GRIDS = {
    "icon-ch1-eps": GRID_DIR / "icon-1/icon_grid_0001_R19B08_mch.nc",
    "icon-ch2-eps": GRID_DIR / "icon-2/icon_grid_0002_R19B07_mch.nc",
}


def split_arg(ctx, param, value: str):
    return [item.strip() for item in value.split(",")]


@click.command()
@click.option(
    "--models",
    type=str,
    default=DEFAULTS["models"],
    callback=split_arg,
    help="Comma separated list of models for which to produce indices and weights.",
)
@click.option(
    "--dst-grids",
    type=str,
    default=DEFAULTS["dst_grids"],
    callback=split_arg,
    help="Comma separated list of destination grids "
    "for which to produce indices and weights.",
)
@click.option(
    "--grid-config-path",
    type=click.Path(path_type=Path),
    default=DEFAULTS["grid_config_path"],
    help="Path to the grid configuration file.",
)
def main(models, dst_grids, grid_config_path):
    Path("output").mkdir(exist_ok=True)
    cfg = read_grid_config(grid_config_path)
    for model in models:
        for dst_grid in dst_grids:
            key = f"{model}-{dst_grid}"
            dst = Grid(**cfg[model][dst_grid])
            input_grid_path = INPUT_GRIDS[model]
            write_coeffs(input_grid_path, key, dst)


@dc.dataclass
class Grid:
    dx: float
    dy: float
    xmin: float
    xmax: float
    ymin: float
    ymax: float
    north_pole_lon: float = -180.0
    north_pole_lat: float = 90.0

    @property
    def nx(self):
        return round((self.xmax - self.xmin) / self.dx + 1)

    @property
    def ny(self):
        return round((self.ymax - self.ymin) / self.dy + 1)

    @property
    def north_pole(self):
        return self.north_pole_lon, self.north_pole_lat


def read_grid_config(config_path: Path):
    with config_path.open() as f:
        return yaml.safe_load(f)


def write_coeffs(input_grid_path: Path, key: str, dst: Grid) -> None:
    fields = [("VN", "U,V", "rbf")]
    inds = xr.open_dataset(input_grid_path, engine="netcdf4")
    sg = rg.RegularLatLonGrid(
        dst.nx,
        dst.ny,
        (dst.xmin, dst.ymin),
        (dst.xmax, dst.ymax),
        dst.north_pole,
    )
    coeffs = ir.compute_icon_grid_coeffs(
        5,
        sgrid=sg,
        ingrid_ds=inds,
        outgrid_type="local-reg",
        fields=fields,
    )
    names = [
        f"rbf{prefix}B{suffix}"
        for prefix in ("_", "_u_vn_", "_v_vn_")
        for suffix in ("_wgt", "_glbidx")
    ]
    n = dst.nx * dst.ny
    output = coeffs[names].isel(
        rbf_B_stencil_size=slice(n),
        rbf_u_vn_B_stencil_size=slice(n),
        rbf_v_vn_B_stencil_size=slice(n),
    )
    output.attrs = {
        "xmin": dst.xmin,
        "xmax": dst.xmax,
        "ymin": dst.ymin,
        "ymax": dst.ymax,
        "nx": dst.nx,
        "ny": dst.ny,
        "dx": dst.dx,
        "dy": dst.dy,
        "north_pole_lon": dst.north_pole_lon,
        "north_pole_lat": dst.north_pole_lat,
    }
    output.to_netcdf(f"output/{key}.nc")


if __name__ == "__main__":
    main()
