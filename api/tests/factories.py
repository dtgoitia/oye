import datetime

from src.config import Config


def get_test_config() -> Config:
    return Config(
        host="0.0.0.0",
        port=5001,
        engine_tick_delta=1,
        debug_mode=True,
        db_uri=":memory:",
    )


def d(raw: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(raw)
