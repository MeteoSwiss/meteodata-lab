"""Test configuration."""

# Standard library
import os
import subprocess
from pathlib import Path

# Third-party
import numpy as np
import pytest
import xarray as xr
from jinja2 import Environment, FileSystemLoader

root = Path(__file__).parents[2]
view_path = str(root / "spack-env/.spack-env/view")
os.environ["ECCODES_DIR"] = view_path


@pytest.fixture(scope="session")
def machine():
    """Machine name."""
    # adapted from spack-c2sm
    path = Path("/etc/xthostname")
    if path.exists():
        return path.read_text().strip()
    hostname = subprocess.check_output(["hostname", "-s"]).decode()
    match hostname.split("-"):
        case "tsa", *_:
            return "tsa"
        case "arolla", *_:
            return "arolla"
    return "unknown"


@pytest.fixture
def unpack(work_dir: Path):
    def f(path: Path) -> Path:
        src = path.with_suffix(".tar.gz")
        if not src.exists():
            return path
        dst = work_dir
        tgt = dst / path.name
        if tgt.exists():
            return tgt
        subprocess.run(["tar", "-xf", str(src), "-C", str(dst)], check=True)
        return tgt

    return f


@pytest.fixture
def data_dir(request, machine, unpack):
    """Base data dir."""
    if machine == "tsa":
        base_dir = Path("/project/s83c/rz+/icon_data_processing_incubator/")
    elif machine == "balfrin":
        base_dir = Path("/store_new/mch/msopr/icon_workflow_2/")
    else:
        return None
    marker = request.node.get_closest_marker("data")
    if marker is None:
        return unpack(base_dir / "datasets/32_39x45_51")
    match marker.args[0]:
        case "original":
            return base_dir / "datasets/original"
        case "reduced":
            return unpack(base_dir / "datasets/32_39x45_51")
        case "reduced-time":
            return unpack(base_dir / "datasets/32_39x45_51") / "COSMO-1E_time"
        case "reduced-ens":
            return unpack(base_dir / "datasets/32_39x45_51") / "COSMO-1E_ens"
        case "flexpart":
            return base_dir / "data/flexpart"
        case "iconremap":
            return base_dir / "datasets/iconremap"
    raise RuntimeError(f"No match for data mark {marker.args[0]}")


@pytest.fixture(scope="session")
def work_dir(tmp_path_factory):
    """Base work dir."""
    return tmp_path_factory.mktemp("data")


@pytest.fixture(scope="session")
def fieldextra_path(machine):
    """Fieldextra path."""
    conf = {
        "tsa": Path("/project/s83c/fieldextra/tsa"),
        "balfrin": Path("/scratch/mch/jenkins/fieldextra/balfrin"),
    }
    return conf.get(machine)


@pytest.fixture(scope="session")
def icon_grid_paths():
    grid_dir = Path("/scratch/mch/jenkins/icon/pool/data/ICON/mch/grids/")
    return {
        "icon-ch1-eps": grid_dir / "icon-1/icon_grid_0001_R19B08_mch.nc",
        "icon-ch2-eps": grid_dir / "icon-2/icon_grid_0002_R19B07_mch.nc",
    }


@pytest.fixture(scope="session")
def template_env():
    """Jinja input namelist template environment."""
    test_dir = Path(__file__).parent
    loader = FileSystemLoader(test_dir / "fieldextra_templates")
    return Environment(loader=loader, keep_trailing_newline=True)


@pytest.fixture(scope="session")
def setup_fdb(machine):
    os.environ["FDB5_DIR"] = view_path
    os.environ["FDB_HOME"] = os.environ["FDB5_DIR"]
    os.environ["FDB5_CONFIG_FILE"] = str(
        root / f"src/meteodatalab/data/fdb_config_{machine}.yaml"
    )


@pytest.fixture(scope="session")
def request_template():
    return {
        "class": "od",
        "date": "20230201",
        "expver": "0001",
        "model": "COSMO-1E",
        "number": 0,
        "step": 0,
        "stream": "enfo",
        "time": "0300",
        "type": "ememb",
    }


@pytest.fixture(scope="session")
def icon_grid(icon_grid_paths):
    """Load the ICON native grid for a given model."""

    def f(model_name: str) -> dict[str, xr.DataArray]:
        grid_path = icon_grid_paths.get(model_name)

        if grid_path is None:
            raise KeyError

        ds = xr.open_dataset(grid_path)

        rad2deg = 180 / np.pi
        result = ds[["clon", "clat"]].reset_coords() * rad2deg
        return {"lon": result.clon, "lat": result.clat}

    return f


@pytest.fixture
def fieldextra(tmp_path, data_dir, template_env, fieldextra_path):
    """Run fieldextra on a given field."""

    def f(
        product: str,
        conf_files: dict[str, str] | None = None,
        load_output: str | list[str] = "00_outfile.nc",
        **ctx,
    ):
        if conf_files is None:
            conf_files = {
                "inputi": data_dir / "COSMO-1E/1h/ml_sl/000/lfff00000000",
                "inputc": data_dir / "COSMO-1E/1h/const/000/lfff00000000c",
                "output": "<HH>_outfile.nc",
            }
        template = template_env.get_template(f"test_{product}.nl")
        nl_path = tmp_path / f"test_{product}.nl"
        ctx["file"] = conf_files
        ctx["resources"] = fieldextra_path / "resources"
        nl_path.write_text(template.render(**ctx))

        executable = str(fieldextra_path / "bin/fieldextra_gnu_opt_omp")
        subprocess.run([executable, str(nl_path)], check=True, cwd=tmp_path)

        if isinstance(load_output, str):
            return xr.open_dataset(tmp_path / load_output).expand_dims("ref_time")
        return [
            xr.open_dataset(tmp_path / filename).expand_dims("ref_time")
            for filename in load_output
        ]

    return f
