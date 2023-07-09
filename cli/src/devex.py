from typing import Never


class UnexpectedScenario(Exception):
    ...


def todo(message: str | None = None) -> Never:
    raise NotImplementedError(message)
