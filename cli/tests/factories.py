import datetime

from src.config import Config


def get_test_config() -> Config:
    return Config(
        oye_api_url="dummy oye api url",
        debug_mode=True,
    )


def d(raw: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(raw)
