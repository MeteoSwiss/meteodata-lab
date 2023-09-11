"""Test configuration."""
# Standard library
import subprocess
from collections.abc import Iterable
from pathlib import Path

# Third-party
import pytest
import xarray as xr
from jinja2 import Environment
from jinja2 import FileSystemLoader


@pytest.fixture
def data_dir():
    """Base data dir."""
    return Path("/project/s83c/rz+/icon_data_processing_incubator/data/SWISS")


@pytest.fixture
def fieldextra_executable():
    """Fieldextra executable."""
    return "/project/s83c/fieldextra/tsa/bin/fieldextra_gnu_opt_omp"


@pytest.fixture
def template_env():
    """Jinja input namelist template environment."""
    test_dir = Path(__file__).parent
    loader = FileSystemLoader(test_dir / "fieldextra_templates")
    return Environment(loader=loader, keep_trailing_newline=True)


@pytest.fixture
def fieldextra(tmp_path, data_dir, template_env, fieldextra_executable):
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
        nl_path.write_text(template.render(file=conf_files, **ctx))

        subprocess.run([fieldextra_executable, str(nl_path)], check=True, cwd=tmp_path)

        if isinstance(hh, int):
            return xr.open_dataset(tmp_path / f"{hh:02d}_{field_name}.nc")
        if isinstance(hh, Iterable):
            return [xr.open_dataset(tmp_path / f"{h:02d}_{field_name}.nc") for h in hh]
        if hh is None:
            return xr.open_dataset(tmp_path / f"{field_name}.nc")
        raise TypeError("Unknown type for param hh")

    return f
