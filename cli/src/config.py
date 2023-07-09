import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    oye_api_url: str
    debug_mode: bool


class ConfigError(Exception):
    ...


def env_var_to_str(name: str) -> str:
    if value := os.environ.get(name):
        return value

    raise ConfigError(f"expected to the {name!r} environment variable to be set, but it is not")


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
        oye_api_url=env_var_to_str("OYE_API_URL"),
        debug_mode=env_var_to_bool("DEBUG", False),
    )

    return config
