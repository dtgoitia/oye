import datetime

from src.domain.reminders import Once, Reminder, ReminderRepository
from tests.factories import d


def test_once_next_occurrence() -> None:
    t = datetime.datetime.now()
    schedule = Once(at=t)
    assert schedule.next_occurrence == t


def test_reminder_manager():
    man = ReminderRepository()

    man.add(
        Reminder(
            id="rem_00000000",
            description="do foo",
            schedule=Once(at=d("2023-07-05 00:00:01 +01:00")),
        ),
    )
    man.add(
        Reminder(
            id="rem_11111111",
            description="do bar",
            schedule=Once(at=d("2023-07-05 00:00:01 +01:00")),
        ),
    )
    man.add(
        Reminder(
            id="rem_22222222",
            description="do baz",
            schedule=Once(at=d("2023-07-05 00:00:09 +01:00")),
        ),
    )
    man.add(
        Reminder(
            id="rem_33333333",
            description="do bazzzz",
            schedule=Once(at=d("2023-07-05 00:00:10 +01:00")),
        ),
    )

    reminders = man.get_reminders_from(
        occurrences=iter(
            [
                d("2023-07-05 00:00:01 +01:00"),
                d("2023-07-05 00:00:09 +01:00"),
            ]
        )
    )
    assert {r.id for r in reminders} == {
        "rem_00000000",
        "rem_11111111",
        "rem_22222222",
        # "rem_33333333"  <--- not this one
    }
