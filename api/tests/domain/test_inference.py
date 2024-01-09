import datetime

import pytest

from src.domain.inference import infer_reminder, infer_timezone
from src.domain.reminders import Once
from tests.factories import d


@pytest.mark.freeze_time("2020-02-03 01:01:06Z")
@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        # only hours
        ("at 9", "2020-02-03 09:00:00+02:00"),
        ("at 17", "2020-02-03 17:00:00+02:00"),
        ("at 5am", "2020-02-03 05:00:00+02:00"),
        ("at 5pm", "2020-02-03 17:00:00+02:00"),
        ("at 5AM", "2020-02-03 05:00:00+02:00"),
        ("at 5PM", "2020-02-03 17:00:00+02:00"),
        # # with ':' separator
        ("at 9:01", "2020-02-03 09:01:00+02:00"),
        ("at 9:15", "2020-02-03 09:15:00+02:00"),
        ("at 17:23", "2020-02-03 17:23:00+02:00"),
        ("at 5:11am", "2020-02-03 05:11:00+02:00"),
        ("at 5:42pm", "2020-02-03 17:42:00+02:00"),
        ("at 5:42PM", "2020-02-03 17:42:00+02:00"),
        ("at 5:11AM", "2020-02-03 05:11:00+02:00"),
        # # with '.' separator
        ("at 9.01", "2020-02-03 09:01:00+02:00"),
        ("at 9.15", "2020-02-03 09:15:00+02:00"),
        ("at 17.23", "2020-02-03 17:23:00+02:00"),
        ("at 5.11am", "2020-02-03 05:11:00+02:00"),
        ("at 5.42pm", "2020-02-03 17:42:00+02:00"),
        ("at 5.42PM", "2020-02-03 17:42:00+02:00"),
        ("at 5.11AM", "2020-02-03 05:11:00+02:00"),
        # # with ' ' separator
        ("at 9 01", "2020-02-03 09:01:00+02:00"),
        ("at 9 15", "2020-02-03 09:15:00+02:00"),
        ("at 17 23", "2020-02-03 17:23:00+02:00"),
        ("at 5 11am", "2020-02-03 05:11:00+02:00"),
        ("at 5 42pm", "2020-02-03 17:42:00+02:00"),
        ("at 5 42PM", "2020-02-03 17:42:00+02:00"),
        ("at 5 11AM", "2020-02-03 05:11:00+02:00"),
    ),
)
def test_infer_at_time(raw: str, expected: str) -> None:
    tz = datetime.timezone(datetime.timedelta(hours=2))

    expected_occurrence = d(expected)

    reminder = infer_reminder(utterance=f"{raw} do foo", tz=tz)
    assert isinstance(reminder.schedule, Once)
    assert reminder.description == "do foo"
    assert reminder.schedule.at == expected_occurrence
    assert reminder.schedule.at.isoformat(sep=" ") == expected

    reminder = infer_reminder(utterance=f"do foo {raw}", tz=tz)
    assert isinstance(reminder.schedule, Once)
    assert reminder.description == "do foo"
    assert reminder.schedule.at == expected_occurrence
    assert reminder.schedule.at.isoformat(sep=" ") == expected


@pytest.mark.freeze_time("2020-02-03 04:05:06Z")
@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        ("in 1 m", "2020-02-03 06:06:06+02:00"),
        ("in 1m", "2020-02-03 06:06:06+02:00"),
        ("in 1 min", "2020-02-03 06:06:06+02:00"),
        ("in 1min", "2020-02-03 06:06:06+02:00"),
        ("in 2 mins", "2020-02-03 06:07:06+02:00"),
        ("in 2mins", "2020-02-03 06:07:06+02:00"),
    ),
)
def test_infer_in_time(raw: str, expected: str) -> None:
    tz = datetime.timezone(datetime.timedelta(hours=2))

    expected_occurrence = d(expected)

    reminder = infer_reminder(utterance=f"{raw} do foo", tz=tz)
    assert isinstance(reminder.schedule, Once)
    assert reminder.description == "do foo"
    assert reminder.schedule.at == expected_occurrence
    assert reminder.schedule.at.isoformat(sep=" ") == expected

    reminder = infer_reminder(utterance=f"do foo {raw}", tz=tz)
    assert isinstance(reminder.schedule, Once)
    assert reminder.description == "do foo"
    assert reminder.schedule.at == expected_occurrence
    assert reminder.schedule.at.isoformat(sep=" ") == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        ("Z", 0),
        ("+02:00", 2),
        ("+10:30", 10.5),
        ("-01:30", -1.5),
        ("+00:00", 0),
    ),
)
def test_infer_timezone(raw: str, expected: int | float) -> None:
    tz = infer_timezone(raw=raw)
    assert tz == datetime.timezone(datetime.timedelta(hours=expected))
