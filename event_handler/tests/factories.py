import datetime

from src.config import Config


def get_test_config() -> Config:
    return Config(
        host="0.0.0.0",
        port=5001,
        server_name="test-server",
        engine_tick_delta=1,
        debug_mode=True,
    )


def d(raw: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(raw)
