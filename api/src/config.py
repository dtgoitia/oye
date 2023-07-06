import os
from dataclasses import dataclass

from src.model import Seconds


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    debug_mode: bool
    engine_tick_delta: Seconds
    server_name: str

    @property
    def api_base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class ConfigError(Exception):
    ...


def env_var_to_bool(name: str, default: bool | None = None) -> bool:
    """
    If no `default` is provided, returns `False`.
    """

    if raw := os.environ.get(name):
        return _to_bool(raw=raw)

    if default is None:
        return False

    return default


def _to_bool(raw: str) -> bool:
    match raw.lower():
        case "true" | "1":
            return True
        case "false" | "0":
            return False
        case _:
            raise ConfigError(f"the value {raw!r} cannot be converted into a boolean")


def get_config() -> Config:
    config = Config(
        debug_mode=env_var_to_bool("DEBUG", False),
        engine_tick_delta=5,
        host="0.0.0.0",
        port=5000,
        server_name="oye",
    )

    return config
