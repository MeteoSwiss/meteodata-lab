"""Test configuration."""
# Standard library
import os
import subprocess
from collections.abc import Iterable
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


@pytest.fixture(scope="session")
def data_dir(machine):
    """Base data dir."""
    if machine == "tsa":
        return Path("/project/s83c/rz+/icon_data_processing_incubator/data/SWISS")
    raise RuntimeError("panic")


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

    def f(field_name, hh: int | Iterable[int] | None = 0, **ctx):
        default_conf_files = {
            "inputi": data_dir / "lfff<DDHH>0000.ch",
            "inputc": data_dir / "lfff00000000c.ch",
            "output": f"<HH>_{field_name}.nc",
        }
        conf_files = ctx.pop("conf_files", default_conf_files)
        template = template_env.get_template(f"test_{field_name}.nl")
        nl_path = tmp_path / f"test_{field_name}.nl"
        ctx["file"] = conf_files
        ctx["resources"] = fieldextra_path / "resources"
        nl_path.write_text(template.render(**ctx))

        executable = str(fieldextra_path / "bin/fieldextra_gnu_opt_omp")
        subprocess.run([executable, str(nl_path)], check=True, cwd=tmp_path)

        if isinstance(hh, int):
            return xr.open_dataset(tmp_path / f"{hh:02d}_{field_name}.nc")
        if isinstance(hh, Iterable):
            return [xr.open_dataset(tmp_path / f"{h:02d}_{field_name}.nc") for h in hh]
        if hh is None:
            return xr.open_dataset(tmp_path / f"{field_name}.nc")
        raise TypeError("Unknown type for param hh")

    return f
