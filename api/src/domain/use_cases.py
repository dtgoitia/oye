import datetime

from src.config import Config
from src.main import Engine, Once, Reminder, ReminderRepository, notify_to_stdout


def initialize_engine(config: Config) -> Engine:
    engine = Engine(
        manager=ReminderRepository(),
        notify_cb=notify_to_stdout,
        config=config,
    )

    def _d(raw: str) -> datetime.datetime:
        return datetime.datetime.fromisoformat(raw)

    reminder_a = Reminder(
        id="rem_00000000",
        description="do foo",
        schedule=Once(at=_d("2023-07-05 00:00:01 +01:00")),
    )
    reminder_b = Reminder(
        id="rem_11111111",
        description="do bar",
        schedule=Once(at=_d("2023-07-05 00:00:13 +01:00")),
    )
    reminder_c = Reminder(
        id="rem_22222222",
        description="do baz",
        schedule=Once(at=_d("2023-07-06 00:00:00 +01:00")),
    )

    engine.add_reminder(reminder_a)
    engine.add_reminder(reminder_b)
    engine.add_reminder(reminder_c)

    return engine
