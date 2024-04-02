"""Mars request helper class."""

# Standard library
import dataclasses as dc
import json
import typing
from collections.abc import Iterable
from enum import Enum
from functools import cache
from importlib.resources import files

# Third-party
import pydantic
import yaml
from pydantic import dataclasses as pdc

ValidationError = pydantic.ValidationError


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


class FeatureType(str, Enum):
    TIMESERIES = "timeseries"


class Point(typing.NamedTuple):
    lat: float
    lon: float


@dc.dataclass(frozen=True)
class TimeseriesFeature:
    type: FeatureType = FeatureType.TIMESERIES
    points: list[Point] = dc.field(default_factory=list)
    start: int = 0
    end: int = 0

    @pydantic.field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v != FeatureType.TIMESERIES:
            raise ValueError("Wrong type")
        return v


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
    param: str | tuple[str, ...]
    date: str | None = None  # YYYYMMDD
    time: str | None = None  # hhmm

    expver: str = "0001"
    levelist: int | tuple[int, ...] | None = None
    number: int | tuple[int, ...] = 0
    step: int | tuple[int, ...] = 0

    class_: Class = dc.field(
        default=Class.OPERATIONAL_DATA,
        metadata=dict(alias="class"),
    )
    levtype: LevType = LevType.MODEL_LEVEL
    model: Model = Model.COSMO_1E
    stream: Stream = Stream.ENS_FORECAST
    type: Type = Type.ENS_MEMBER

    feature: TimeseriesFeature | None = None

    def dump(self):
        if pydantic.__version__.startswith("1"):
            json_str = json.dumps(self, default=pydantic.json.pydantic_encoder)
            obj = json.loads(json_str.replace("class_", "class"))
            return {key: value for key, value in obj.items() if value is not None}

        root = pydantic.RootModel(self)
        return root.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        )

    def _param_id(self):
        mapping = _load_mapping()
        if isinstance(self.param, Iterable) and not isinstance(self.param, str):
            return [mapping[param]["cosmo"]["paramId"] for param in self.param]
        return mapping[self.param]["cosmo"]["paramId"]

    def _staggered(self):
        mapping = _load_mapping()
        if isinstance(self.param, Iterable) and not isinstance(self.param, str):
            return any(
                mapping[param]["cosmo"].get("vertStag", False) for param in self.param
            )
        return mapping[self.param]["cosmo"].get("vertStag", False)

    def to_fdb(self) -> dict[str, typing.Any]:
        if self.date is None or self.time is None:
            raise RuntimeError("date and time are required fields for FDB.")

        if self.levelist is None and self.levtype == LevType.MODEL_LEVEL:
            n_lvl = N_LVL[self.model]
            if self._staggered():
                n_lvl += 1
            levelist: int | tuple[int, ...] | None = tuple(range(1, n_lvl + 1))
        else:
            levelist = self.levelist

        obj = dc.replace(self, levelist=levelist)
        out = typing.cast(dict[str, typing.Any], obj.dump())
        return out | {"param": self._param_id()}
