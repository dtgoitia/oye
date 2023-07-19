from datetime import datetime

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
def test_infer_at_time(raw: str, expected: datetime) -> None:
    expected_occurrence = d(expected)

    reminder = infer_reminder(utterance=f"{raw} do foo")
    assert reminder.description == "do foo"
    assert reminder.schedule.at == expected_occurrence

    reminder = infer_reminder(utterance=f"do foo {raw}")
    assert reminder.description == "do foo"
    assert reminder.schedule.at == expected_occurrence


@pytest.mark.freeze_time("2020-02-03 04:05:06Z")
@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        pytest.param(
            "do stuff in 1 m",
            Once(at=d("2020-02-03 04:06:06Z")),
            id="in_1_m_with_space",
        ),
        pytest.param(
            "do stuff in 1m",
            Once(at=d("2020-02-03 04:06:06Z")),
            id="in_1_m_without_space",
        ),
        pytest.param(
            "do stuff in 1 min",
            Once(at=d("2020-02-03 04:06:06Z")),
            id="in_1_min_with_space",
        ),
        pytest.param(
            "do stuff in 1min",
            Once(at=d("2020-02-03 04:06:06Z")),
            id="in_1_min_without_space",
        ),
        pytest.param(
            "do stuff in 2 mins",
            Once(at=d("2020-02-03 04:07:06Z")),
            id="in_2_mins_with_space",
        ),
        pytest.param(
            "do stuff in 2mins",
            Once(at=d("2020-02-03 04:07:06Z")),
            id="in_2_mins_without_space",
        ),
        pytest.param(
            "do stuff in at 9pm",
            Once(at=d("2020-02-03 21:00:00Z")),
            id="at_9_pm_without_space",
        ),
        pytest.param(
            "do stuff in at 9 pm",
            Once(at=d("2020-02-03 21:00:00Z")),
            id="at_9_pm_with_space",
        ),
        pytest.param(
            "do stuff in at 9.00pm",
            Once(at=d("2020-02-03 21:00:00Z")),
            id="at_900_pm_with_dot_and_without_space",
        ),
        pytest.param(
            "do stuff in at 9.00 pm",
            Once(at=d("2020-02-03 21:00:00Z")),
            id="at_900_pm_with_dot_and_with_space",
        ),
        pytest.param(
            "do stuff in at 9:00pm",
            Once(at=d("2020-02-03 21:00:00Z")),
            id="at_900_pm_with_colon_and_without_space",
        ),
        pytest.param(
            "do stuff in at 9:00 pm",
            Once(at=d("2020-02-03 21:00:00Z")),
            id="at_900_pm_with_colon_and_with_space",
        ),
    ),
)
def test_infer(raw: str, expected: Once) -> None:
    reminder = infer_reminder(utterance=raw)

    assert isinstance(reminder.schedule, Once)
    assert reminder.description == "do stuff"
    assert reminder.schedule.at == expected.at
