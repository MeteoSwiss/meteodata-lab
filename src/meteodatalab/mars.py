"""Mars request helper class."""

from __future__ import annotations

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
    BOUNDINGBOX = "boundingbox"
    TIMESERIES = "timeseries"


class Point(typing.NamedTuple):
    lat: float
    lon: float


@dc.dataclass(frozen=True)
class Range:
    start: int
    end: int
    step: int | None = None


@dc.dataclass(frozen=True)
class BoundingBoxFeature:
    points: list[tuple[float, ...]]
    axes: tuple[str, ...] = ("latitude", "longitude")
    type: typing.Literal[FeatureType.BOUNDINGBOX] = FeatureType.BOUNDINGBOX

    @pydantic.model_validator(mode="after")
    def validate(self):
        possible_axes = {("latitude", "longitude"), ("latitude", "longitude", "level")}
        if len(self.points) != 2:
            raise ValueError("points must contain two points")
        if self.axes not in possible_axes:
            msg = "axes must be a sequence of latitude, longitude and optionally level"
            raise ValueError(msg)
        if any(len(point) != len(self.axes) for point in self.points):
            raise ValueError("points must have same number of components as axes")
        return self


@dc.dataclass(frozen=True)
class TimeseriesFeature:
    points: list[Point]
    time_axis: typing.Literal["step", "date"]
    range: Range | None = None
    axes: tuple[str, str] = ("latitude", "longitude")
    type: typing.Literal[FeatureType.TIMESERIES] = FeatureType.TIMESERIES

    def validate_request(self, request: Request) -> None:
        time_attr = getattr(request, self.time_axis)
        if self.range is not None and time_attr is not None:
            raise ValueError(
                f"only one of {self.time_axis} or feature range must be defined"
            )
        elif self.range is None and time_attr is None:
            raise ValueError(
                f"one of {self.time_axis} or feature range must be defined"
            )


Feature = BoundingBoxFeature | TimeseriesFeature


@cache
def _load_mapping():
    mapping_path = files("meteodatalab.data").joinpath("field_mappings.yml")
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
    number: int | tuple[int, ...] | None = None
    step: int | tuple[int, ...] | None = None

    class_: Class = dc.field(
        default=Class.OPERATIONAL_DATA,
        metadata=dict(alias="class"),
    )
    levtype: LevType = LevType.MODEL_LEVEL
    model: Model = Model.COSMO_1E
    stream: Stream = Stream.ENS_FORECAST
    type: Type = Type.ENS_MEMBER

    feature: Feature | None = dc.field(
        default=None,
        metadata=dict(discriminator="type"),
    )

    @pydantic.model_validator(mode="after")
    def validate(self):
        if isinstance(self.feature, TimeseriesFeature):
            self.feature.validate_request(self)
        return self

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

    def to_polytope(self) -> dict[str, typing.Any]:
        result = self.to_fdb()
        if isinstance(result["param"], list):
            param: str | list[str] = [str(p) for p in result["param"]]
        else:
            param = str(result["param"])
        return result | {"param": param, "model": result["model"].lower()}
