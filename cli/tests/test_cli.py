import pytest

from src import use_cases
from src.config import get_config


@pytest.mark.skip(reason="end-to-end")
def test_2e2() -> None:
    config = get_config()
    added = use_cases.add_reminder(utterance="do stuff in 5 mins", config=config)

    assert added.description == "do stuff"

    fetched = use_cases.get_reminder(reminder_id=added.id, config=config)
    assert added == fetched

    deleted = use_cases.delete_reminder(reminder_id=fetched.id, config=config)
    assert added == deleted

    alread_deleted = use_cases.get_reminder(reminder_id=added.id, config=config)
    assert not alread_deleted

    # added = use_cases.add_reminder(utterance="do stuff in 5 mins", config=config)
    # use_cases.delete_reminder_interactive(config=config)
