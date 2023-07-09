from src import use_cases
from src.config import get_config


def test_2e2() -> None:
    config = get_config()
    added = use_cases.add_reminder(utterance="do stuff in 5 mins", config=config)

    assert added.description == "do stuff"
