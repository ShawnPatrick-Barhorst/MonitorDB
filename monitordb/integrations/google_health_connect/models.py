from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field

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


class StepsItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    count: int
    start_time: datetime
    end_time: datetime


class MetaDataItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    app_version: str
    data_origin: str
    batch_timestamp: datetime
