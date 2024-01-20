import datetime
from typing import Any

from src.config import Config, Secret
from src.domain.reminders import Occurrence, Once, Reminder, generate_reminder_id
from src.model import ReminderId


def get_test_config() -> Config:
    return Config(
        host="0.0.0.0",
        port=5001,
        engine_tick_delta=1,
        debug_mode=True,
        db_uri=":memory:",
        telegram_api_token=Secret("invalid-telegram-api-token"),
    )


def d(raw: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(raw)


def build_reminder(
    id: ReminderId | None = None,
    description: str | None = None,
    schedule: Once | None = None,
    next_occurrence: Occurrence | None = None,
    dispatched: bool | None = None,
) -> Reminder:
    params: dict[str, Any] = {
        "id": generate_reminder_id(),
        "description": "test_description",
    }

    if id is not None:
        params["id"] = id
    if description is not None:
        params["description"] = description
    if schedule is not None:
        params["schedule"] = schedule
    if next_occurrence is not None:
        params["next_occurrence"] = next_occurrence
    if dispatched is not None:
        params["dispatched"] = dispatched

    return Reminder(**params)
