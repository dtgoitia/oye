import pytest

from src.domain.inference import infer_reminder
from src.domain.reminders import Once
from tests.factories import d


@pytest.mark.freeze_time("2020-02-03 01:01:06Z")
@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        # only hours
        ("at 9", "2020-02-03 09:00:00"),
        ("at 17", "2020-02-03 17:00:00"),
        ("at 5am", "2020-02-03 05:00:00"),
        ("at 5pm", "2020-02-03 17:00:00"),
        ("at 5AM", "2020-02-03 05:00:00"),
        ("at 5PM", "2020-02-03 17:00:00"),
        # # with ':' separator
        ("at 9:01", "2020-02-03 09:01:00"),
        ("at 9:15", "2020-02-03 09:15:00"),
        ("at 17:23", "2020-02-03 17:23:00"),
        ("at 5:11am", "2020-02-03 05:11:00"),
        ("at 5:42pm", "2020-02-03 17:42:00"),
        ("at 5:42PM", "2020-02-03 17:42:00"),
        ("at 5:11AM", "2020-02-03 05:11:00"),
        # # with '.' separator
        ("at 9.01", "2020-02-03 09:01:00"),
        ("at 9.15", "2020-02-03 09:15:00"),
        ("at 17.23", "2020-02-03 17:23:00"),
        ("at 5.11am", "2020-02-03 05:11:00"),
        ("at 5.42pm", "2020-02-03 17:42:00"),
        ("at 5.42PM", "2020-02-03 17:42:00"),
        ("at 5.11AM", "2020-02-03 05:11:00"),
        # # with ' ' separator
        ("at 9 01", "2020-02-03 09:01:00"),
        ("at 9 15", "2020-02-03 09:15:00"),
        ("at 17 23", "2020-02-03 17:23:00"),
        ("at 5 11am", "2020-02-03 05:11:00"),
        ("at 5 42pm", "2020-02-03 17:42:00"),
        ("at 5 42PM", "2020-02-03 17:42:00"),
        ("at 5 11AM", "2020-02-03 05:11:00"),
    ),
)
def test_infer_at_time(raw: str, expected: str) -> None:
    expected_occurrence = d(expected)

    reminder = infer_reminder(utterance=f"{raw} do foo")
    assert isinstance(reminder.schedule, Once)
    assert reminder.description == "do foo"
    assert reminder.schedule.at == expected_occurrence

    reminder = infer_reminder(utterance=f"do foo {raw}")
    assert isinstance(reminder.schedule, Once)
    assert reminder.description == "do foo"
    assert reminder.schedule.at == expected_occurrence


@pytest.mark.freeze_time("2020-02-03 04:05:06Z")
@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        ("in 1 m", "2020-02-03 04:06:06Z"),
        ("in 1m", "2020-02-03 04:06:06Z"),
        ("in 1 min", "2020-02-03 04:06:06Z"),
        ("in 1min", "2020-02-03 04:06:06Z"),
        ("in 2 mins", "2020-02-03 04:07:06Z"),
        ("in 2mins", "2020-02-03 04:07:06Z"),
    ),
)
def test_infer_in_time(raw: str, expected: str) -> None:
    expected_occurrence = d(expected)

    reminder = infer_reminder(utterance=f"{raw} do foo")
    assert isinstance(reminder.schedule, Once)
    assert reminder.description == "do foo"
    assert reminder.schedule.at == expected_occurrence

    reminder = infer_reminder(utterance=f"do foo {raw}")
    assert isinstance(reminder.schedule, Once)
    assert reminder.description == "do foo"
    assert reminder.schedule.at == expected_occurrence
