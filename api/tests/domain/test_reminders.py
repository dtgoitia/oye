import datetime

import pytest

from src.domain.reminders import Once, Reminder, ReminderRepository, Scenario, identify_scenario
from tests.factories import build_reminder, d


def test_once_next_occurrence() -> None:
    t = datetime.datetime.now()
    schedule = Once(at=t)
    assert schedule.next_occurrence == t


@pytest.mark.skip(reason="needs fixing or removing once POC is complete")
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


@pytest.mark.parametrize(
    ("reminder", "now", "expected"),
    (
        pytest.param(
            build_reminder(
                schedule=Once(at=d("2024-01-17 00:00:01 +01:00")),
                next_occurrence=None,
                dispatched=True,
            ),
            d("2024-01-20 00:00:00 +01:00"),
            Scenario.invalid_reminder,
            id="invalid_state",
        ),
        pytest.param(
            build_reminder(
                schedule=Once(at=d("2024-01-17 00:00:01 +01:00")),
                next_occurrence=None,
                dispatched=False,
            ),
            d("2024-01-20 00:00:00 +01:00"),
            Scenario.awaiting_for_next_occurrence_to_be_calculated,
            id=Scenario.awaiting_for_next_occurrence_to_be_calculated.name,
        ),
        pytest.param(
            build_reminder(
                schedule=Once(at=d("2024-01-17 00:00:01 +01:00")),
                next_occurrence=d("2024-01-17 00:00:01 +01:00"),
                dispatched=True,
            ),
            d("2024-01-20 00:00:00 +01:00"),
            Scenario.dispatched_reminder,
            id=Scenario.dispatched_reminder.name,
        ),
        pytest.param(
            build_reminder(
                schedule=Once(at=d("2024-01-17 00:00:01 +01:00")),
                next_occurrence=d("2024-01-17 00:00:01 +01:00"),
                dispatched=False,
            ),
            d("2024-01-20 00:00:00 +01:00"),
            Scenario.reminder_to_be_dispatched,
            id=Scenario.reminder_to_be_dispatched.name,
        ),
        pytest.param(
            build_reminder(
                schedule=Once(at=d("2024-01-27 00:00:00 +01:00")),
                next_occurrence=d("2024-01-27 00:00:00 +01:00"),
                dispatched=True,
            ),
            d("2024-01-20 00:00:00 +01:00"),
            Scenario.invalid_reminder,
            id=Scenario.invalid_reminder.name,
        ),
        pytest.param(
            build_reminder(
                schedule=Once(at=d("2024-01-27 00:00:00 +01:00")),
                next_occurrence=d("2024-01-27 00:00:00 +01:00"),
                dispatched=False,
            ),
            d("2024-01-20 00:00:00 +01:00"),
            Scenario.reminder_to_be_dispatched,
            id=Scenario.reminder_to_be_dispatched.name,
        ),
    ),
)
def test_identify_scenario(reminder: Reminder, now: datetime.datetime, expected: Scenario) -> None:
    scenario = identify_scenario(reminder=reminder, now=now)
    assert scenario == expected
