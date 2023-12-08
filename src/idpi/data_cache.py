"""Helper class to cache data.

The helper is intended to create a cache of grib files with a layout that is
suitable for reading by fieldextra.

"""


# Standard library
import dataclasses as dc
from itertools import product
from pathlib import Path

# Local
from . import data_source

DEFAULT_FILES = {
    "inputi": "<mmm>/lfff<ddhh>0000",
    "inputc": "<mmm>/lfff00000000c",
}


@dc.dataclass
class DataCache:
    cache_dir: Path
    fields: dict[str, list]
    files: dict[str, str] = dc.field(default_factory=lambda: DEFAULT_FILES)
    steps: list[int] = dc.field(default_factory=lambda: [0])
    numbers: list[int] = dc.field(default_factory=lambda: [0])
    _populated: list[Path] = dc.field(default_factory=list, init=False)

    def __post_init__(self):
        if not self.fields.keys() <= self.files.keys():
            raise ValueError("fields keys must be a subset of files keys")

    @property
    def conf_files(self) -> dict[str, Path]:
        return {
            label: self.cache_dir / pattern for label, pattern in self.files.items()
        }

    def _iter_files(self):
        # support more patterns ?
        # https://github.com/COSMO-ORG/fieldextra/blob/develop/documentation/README.user#L2797
        patterns = (
            ("<mmm>", "{mmm:03d}"),
            ("<ddhh>", "{dd:02d}{hh:02d}"),
        )
        for label, name in self.files.items():
            name = name.lower()
            numbers = self.numbers if "<mmm>" in name else [None]
            steps = self.steps if "<ddhh>" in name else [None]
            for src, dst in patterns:
                name = name.replace(src, dst)
            for number, step in product(numbers, steps):
                dd = step // 24 if step is not None else None
                hh = step % 24 if step is not None else None
                yield label, name.format(mmm=number, dd=dd, hh=hh), number, step

    def _iter_requests(self, label: str, number: int | None, step: int | None):
        param_map: dict[str, list[str]] = {}
        for param, levtype in self.fields[label]:
            param_map.setdefault(levtype, []).append(param)

        for levtype, params in param_map.items():
            req = {"param": params, "levtype": levtype}
            if number is not None:
                req["number"] = number
            if step is not None:
                req["step"] = step
            yield req

    def populate(self, source: data_source.DataSource):
        for label, rel_path, number, step in self._iter_files():
            path = self.cache_dir / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)

            with path.open("ba") as f:
                for req in self._iter_requests(label, number, step):
                    for field in source.retrieve(req):
                        f.write(field.message())

            self._populated.append(path)

    def clear(self):
        for path in self._populated:
            path.unlink()
