"""Test configuration."""

# Standard library
import os
import subprocess
from pathlib import Path

# Third-party
import pytest
import xarray as xr
from jinja2 import Environment, FileSystemLoader


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
def data_dir(request, machine):
    """Base data dir."""
    if machine != "tsa":
        return None
    base_dir = Path("/project/s83c/rz+/icon_data_processing_incubator/")
    marker = request.node.get_closest_marker("data")
    if marker is None:
        return base_dir / "datasets/32_39x45_51"
    match marker.args[0]:
        case "original":
            return base_dir / "datasets/original"
        case "reduced":
            return base_dir / "datasets/32_39x45_51"
        case "reduced-time":
            return base_dir / "datasets/32_39x45_51/COSMO-1E_time"
        case "reduced-ens":
            return base_dir / "datasets/32_39x45_51/COSMO-1E_ens"
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
        "balfrin": Path("/users/tsm/proj.aare/fieldextra/v14.3.1/"),
    }
    return conf[machine]


@pytest.fixture(scope="session")
def template_env():
    """Jinja input namelist template environment."""
    test_dir = Path(__file__).parent
    loader = FileSystemLoader(test_dir / "fieldextra_templates")
    return Environment(loader=loader, keep_trailing_newline=True)


@pytest.fixture(scope="session")
def setup_fdb(machine):
    root = Path(__file__).parents[2]

    os.environ["FDB5_DIR"] = str(root / "spack-env/.spack-env/view")
    os.environ["FDB_HOME"] = os.environ["FDB5_DIR"]
    os.environ["FDB5_CONFIG_FILE"] = str(
        root / f"src/idpi/data/fdb_config_{machine}.yaml"
    )


@pytest.fixture(scope="session")
def request_template():
    return {
        "class": "od",
        "date": "20230201",
        "expver": "0001",
        "model": "COSMO-1E",
        "stream": "enfo",
        "time": "0300",
        "type": "ememb",
    }


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
            return xr.open_dataset(tmp_path / load_output)
        return [xr.open_dataset(tmp_path / filename) for filename in load_output]

    return f
