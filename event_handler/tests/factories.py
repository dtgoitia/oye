import datetime

from src.config import Config


def get_test_config() -> Config:
    return Config(
        debug_mode=True,
        tick_interval=1,
    )


def d(raw: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(raw)
