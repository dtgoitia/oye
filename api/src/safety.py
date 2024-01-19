"""
Credit: https://jellis18.github.io/post/2021-12-13-python-exceptions-rust-go/
"""

from typing import Any, Callable, Generic, NoReturn, TypeVar

T = TypeVar("T")
E = TypeVar("E", bound=BaseException)


class Ok(Generic[T, E]):
    _value: T
    __match_args__ = ("_value",)

    def __init__(self, value: T):
        self._value = value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Ok):
            return self._value == other._value
        return False

    def unwrap(self) -> T:
        """
        Return the wrapped value.
        """
        return self._value

    def unwrap_or(self, default: T) -> T:
        """
        If OK, return the wrapped value. Otherwise, return the provided
        `default` value.
        """
        return self.unwrap()

    def unwrap_or_else(self, op: Callable[[E], T]) -> T:
        """
        If OK, return the wrapped value. Otherwise, handle the wrapped error
        value with the provided `op` function.
        """
        return self.unwrap()

    def __repr__(self) -> str:
        return f"Ok({repr(self._value)})"


class Err(Generic[T, E]):
    _err: E
    __match_args__ = ("_err",)

    def __init__(self, err: E):
        self._err = err

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Err):
            return self._err == other._err
        return False

    def unwrap(self) -> NoReturn:
        """
        Return the wrapped value.
        """
        raise self._err

    def unwrap_or(self, default: T) -> T:
        """
        If OK, return the wrapped value. Otherwise, return the provided
        `default` value.
        """
        return default

    def unwrap_or_else(self, op: Callable[[E], T]) -> T:
        """
        If OK, return the wrapped value. Otherwise, handle the wrapped error
        value with the provided `op` function.
        """
        return op(self._err)

    def __repr__(self) -> str:
        return f"Err({repr(self._err)})"


Result = Ok[T, E] | Err[T, E]
