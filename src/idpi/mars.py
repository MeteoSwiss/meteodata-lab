"""Mars request helper class."""

# Standard library
import dataclasses as dc
from enum import Enum
from functools import cache
from importlib.resources import files

# Third-party
import pydantic
import yaml
from pydantic import dataclasses as pdc


class Class(str, Enum):
    OPERATIONAL_DATA = "od"


class LevType(str, Enum):
    MODEL_LEVEL = "ml"
    PRESSURE_LEVEL = "pl"
    SURFACE = "sfc"
    SURFACE_OTHER = "sol"
    POT_VORTICITY = "pv"
    POT_TEMPERATURE = "pt"
    DEPTH = "dp"


class Model(str, Enum):
    COSMO_1E = "COSMO-1E"
    COSMO_2E = "COSMO-2E"
    KENDA_1 = "KENDA-1"
    SNOWPOLINO = "SNOWPOLINO"
    ICON_CH1_EPS = "ICON-CH1-EPS"
    ICON_CH2_EPS = "ICON-CH2-EPS"
    KENDA_CH1 = "KENDA-CH1"


class Stream(str, Enum):
    ENS_DATA_ASSIMIL = "enda"
    ENS_FORECAST = "enfo"


class Type(str, Enum):
    DETERMINISTIC = "det"
    ENS_MEMBER = "ememb"
    ENS_MEAN = "emean"
    ENS_STD_DEV = "estdv"


@cache
def _load_mapping():
    mapping_path = files("idpi.data").joinpath("field_mappings.yml")
    return yaml.safe_load(mapping_path.open())


N_LVL = {
    Model.COSMO_1E: 80,
    Model.COSMO_2E: 60,
}


@pdc.dataclass(
    frozen=True,
    config=pydantic.ConfigDict(use_enum_values=True),
)
class Request:
    param: str | int
    date: str | None = None  # YYYYMMDD
    time: str | None = None  # hhmm

    expver: str = "0001"
    levelist: int | tuple[int, ...] | None = None
    number: int | tuple[int, ...] = 1
    step: int | tuple[int, ...] = 0

    class_: Class = dc.field(
        default=Class.OPERATIONAL_DATA,
        metadata=dict(alias="class"),
    )
    levtype: LevType = LevType.MODEL_LEVEL
    model: Model = Model.COSMO_1E
    stream: Stream = Stream.ENS_FORECAST
    type: Type = Type.ENS_MEMBER

    def dump(self, exclude_defaults: bool = False):
        root = pydantic.RootModel(self)
        return root.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            exclude_defaults=exclude_defaults,
        )

    def to_fdb(self):
        mapping = _load_mapping()
        param_id = mapping[self.param]["cosmo"]["paramId"]
        staggered = mapping[self.param]["cosmo"].get("vertStag", False)

        if self.levelist is None and self.levtype == LevType.MODEL_LEVEL:
            n_lvl = N_LVL[self.model]
            if staggered:
                n_lvl += 1
            levelist = tuple(range(1, n_lvl + 1))
        else:
            levelist = self.levelist

        obj = dc.replace(self, param=param_id, levelist=levelist)
        return obj.dump(exclude_defaults=False)
