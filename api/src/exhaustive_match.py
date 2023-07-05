from typing import Never

from src.devex import UnexpectedScenario


def assert_never(message: str) -> Never:
    raise UnexpectedScenario(message)
