import pytest

from src.domain.inference import infer_reminder
from src.domain.reminders import Once
from tests.factories import d


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
            id="in_1_m_wihout_space",
        ),
        pytest.param(
            "do stuff in 1 min",
            Once(at=d("2020-02-03 04:06:06Z")),
            id="in_1_min_with_space",
        ),
        pytest.param(
            "do stuff in 1min",
            Once(at=d("2020-02-03 04:06:06Z")),
            id="in_1_min_wihout_space",
        ),
        pytest.param(
            "do stuff in 2 mins",
            Once(at=d("2020-02-03 04:07:06Z")),
            id="in_2_mins_with_space",
        ),
        pytest.param(
            "do stuff in 2mins",
            Once(at=d("2020-02-03 04:07:06Z")),
            id="in_2_mins_wihout_space",
        ),
    ),
)
def test_infer(raw: str, expected: Once) -> None:
    reminder = infer_reminder(utterance=raw)

    assert isinstance(reminder.schedule, Once)
    assert reminder.description == "do stuff"
    assert reminder.schedule.at == expected.at
