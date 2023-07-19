from datetime import datetime
import pytest

from src.domain.inference import infer_reminder
from src.domain.reminders import Once
from tests.factories import d

@pytest.mark.freeze_time("2020-02-03 04:05:06Z")
@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        ("9 foo", midnight + datetime.timedelta(hours=9, minutes=0)),
        ("17 foo", midnight + datetime.timedelta(hours=17, minutes=0)),
        ("5am foo", midnight + datetime.timedelta(hours=5, minutes=0)),
        ("5pm foo", midnight + datetime.timedelta(hours=17, minutes=0)),
        ("5AM foo", midnight + datetime.timedelta(hours=5, minutes=0)),
        ("5PM foo", midnight + datetime.timedelta(hours=17, minutes=0)),
    )
)
def test_infer_time_only_hour(raw: str, expected: datetime) -> None

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
