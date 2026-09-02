from datetime import datetime
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    computed_field,
    model_validator,
)

Decimal3 = Annotated[float, AfterValidator(lambda x: round(x, 3))]

SLEEP_STAGE_MAP = {
    0: "Unknown",
    1: "Awake",
    2: "Generic Sleep",
    3: "Out of Bed",
    4: "Light Sleep",
    5: "Deep Sleep",
    6: "REM Sleep",
}


class SleepStageItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    stage: int
    start_time: datetime
    end_time: datetime
    duration_seconds: int

    @computed_field
    @property
    def stage_name(self) -> str:
        return SLEEP_STAGE_MAP.get(self.stage, "Error")


class SleepSessionItem(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Keep only defined features

    session_end_time: datetime
    duration_seconds: int
    stages: list[SleepStageItem] = []


class HeartRateItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bpm: int
    time: datetime

    @model_validator(mode="before")
    @classmethod
    def fall_back_to_avg(cls, data):
        if isinstance(data, dict) and data.get("bpm") is None and "avg" in data:
            data = {**data, "bpm": data["avg"]}
        return data


class NutritionLogItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    calories: Decimal3
    protein_grams: Decimal3
    carbs_grams: Decimal3
    fat_grams: Decimal3
    sugar_grams: Decimal3
    sodium_grams: Decimal3
    dietary_fiber_grams: Decimal3
    name: str
    start_time: datetime
    end_time: datetime


class StepsItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    count: int
    start_time: datetime
    end_time: datetime


class OxygenSaturationItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    time: datetime
    percentage: float

    @model_validator(mode="before")
    @classmethod
    def fall_back_to_avg(cls, data):
        if isinstance(data, dict) and data.get("percentage") is None and "avg" in data:
            data = {**data, "percentage": data["avg"]}
        return data


class MetaDataItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    app_version: str
    data_origin: str
    batch_timestamp: datetime
