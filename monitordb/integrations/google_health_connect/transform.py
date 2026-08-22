from pydantic import TypeAdapter

from monitordb.integrations.google_health_connect.models import (
    HeartRateItem,
    NutritionLogItem,
    SleepSessionItem,
)

SLEEP_SESSION_ADAPTER = TypeAdapter(list[SleepSessionItem])
HEART_RATE_ADAPTER = TypeAdapter(list[HeartRateItem])
NUTRITION_LOG_ITEM = TypeAdapter(list[NutritionLogItem])


def parse_sleep_sessions(raw_sessions: list[dict]) -> list[SleepSessionItem]:
    return SLEEP_SESSION_ADAPTER.validate_python(raw_sessions)


def parse_heart_rate(raw_heart_rate: list[dict]) -> list[HeartRateItem]:
    return HEART_RATE_ADAPTER.validate_python(raw_heart_rate)


def parse_nutrition_log(raw_nutrition_log: list[dict]) -> list[NutritionLogItem]:
    return NUTRITION_LOG_ITEM.validate_python(raw_nutrition_log)
