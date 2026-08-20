from pydantic import TypeAdapter

from monitordb.integrations.google_health_connect.models import (
    SleepSessionItem,
)

SLEEP_SESSION_ADAPTER = TypeAdapter(list[SleepSessionItem])
# SLEEP_STAGE_ADAPTER = TypeAdapter(list[SleepStageItem])


def parse_sleep_sessions(raw_sessions: list[dict]) -> list[SleepSessionItem]:
    return SLEEP_SESSION_ADAPTER.validate_python(raw_sessions)


# def parse_sleep_stages(raw_stages: list[dict]) -> list[SleepStageItem]:
#     return SLEEP_STAGE_ADAPTER.validate_python(raw_stages)
