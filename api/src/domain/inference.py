import datetime
import enum
import re
from typing import Literal

from src.devex import UnexpectedScenario
from src.domain.reminders import Description, NewReminder, Occurrence, Once, Schedule
from src.exhaustive_match import assert_never
from src.model import IsoTimezone, Utterance

STARTS_WITH_IN = re.compile(r"^in (?P<amount>[0-9]+)\s*(?P<unit>[a-zA-Z]+) (?P<description>.*)$")
ENDS_WITH_IN = re.compile(r"^(?P<description>.*) in (?P<amount>[0-9]+)\s*(?P<unit>[a-zA-Z]+)$")
STARTS_WITH_AT = re.compile(r"^at (?P<when>[0-9\.\:\sampAMP]+) (?P<description>.*)$")
ENDS_WITH_AT = re.compile(r"^(?P<description>.*) at (?P<when>[0-9\.\:\sampAMP]+)$")

# ======================================================================================
# RegEx patterns to parse 'at ...'
HOUR_PATTERN = r"(?P<hour>[0-2]?[0-9])"
HOUR_AND_MIN_SEPARATOR = r"(\s|\:|\.)"
MINS_PATTERN = r"(?P<min>[0-5][0-9])"
AM_PM_PATTERN = r"(?P<am_pm>([ap]m|[AP]M))"
PARSE_TIME_PATTERN = re.compile(
    rf"^{HOUR_PATTERN}{HOUR_AND_MIN_SEPARATOR}?{MINS_PATTERN}?\s?{AM_PM_PATTERN}?"
)
# ======================================================================================

TIMEZONE_PATTERN = re.compile(r"(?P<sign>[\+\-]{1})(?P<hours>[0-2][0-9]):(?P<mins>[0-5][0-9])")


class AmountMustBeNumeric(Exception):
    ...


class InferenceFailed(Exception):
    ...


class UnsupportedTimeUnit(Exception):
    ...


class TimeUnit(enum.Enum):
    days = "days"
    hour = "hour"
    minute = "minute"
    second = "second"


def _infer_time_unit(raw: str) -> TimeUnit:
    match raw:
        case "day" | "days":
            return TimeUnit.days
        case "h" | "hour" | "hours":
            return TimeUnit.hour
        case "m" | "min" | "mins" | "minute" | "minutes":
            return TimeUnit.minute
        case "s" | "sec" | "secs" | "second" | "seconds":
            return TimeUnit.second
        case _:
            raise UnsupportedTimeUnit(f"{raw!r} is not a supported time unit")


def _infer_delta(raw_amount: str, raw_unit: str) -> datetime.timedelta:
    try:
        amount = int(raw_amount)
    except ValueError:
        raise AmountMustBeNumeric(f"expected a numeric amount, but got {raw_amount!r}")

    unit = _infer_time_unit(raw_unit)

    match unit:
        case TimeUnit.days:
            return datetime.timedelta(days=amount)
        case TimeUnit.hour:
            return datetime.timedelta(hours=amount)
        case TimeUnit.minute:
            return datetime.timedelta(minutes=amount)
        case TimeUnit.second:
            return datetime.timedelta(seconds=amount)
        case _:
            assert_never(f"Unsupported time unit: {unit}")


def _infer_starts_with_in_x_time(raw: str, tz: datetime.timezone) -> tuple[Description, Once]:
    """
    Return the Schedule for an utterance like 'in 3 mins ...'.
    """
    match = STARTS_WITH_IN.match(raw)
    if not match:
        raise InferenceFailed(f"expected to start with 'in X min', but got {raw} instead")

    description = match.group("description")
    amount = match.group("amount")
    unit = match.group("unit")

    at = datetime.datetime.now(tz=tz) + _infer_delta(raw_amount=amount, raw_unit=unit)
    schedule = Once(at=at)
    return description, schedule


def _infer_ends_with_in_x_time(raw: str, tz: datetime.timezone) -> tuple[Description, Once]:
    """
    Return the Schedule for an utterance like '... in 3 mins'.
    """

    match = ENDS_WITH_IN.match(raw)
    if not match:
        raise InferenceFailed(f"expected to end with 'in X min', but got {raw} instead")

    description = match.group("description")
    amount = match.group("amount")
    unit = match.group("unit")

    at = datetime.datetime.now(tz=tz) + _infer_delta(raw_amount=amount, raw_unit=unit)
    schedule = Once(at=at)
    return description, schedule


def start_of_today(tz: datetime.timezone) -> datetime.datetime:
    today = datetime.date.today()
    return datetime.datetime(year=today.year, month=today.month, day=today.day, tzinfo=tz)


def _infer_at_time(raw: str, tz: datetime.timezone) -> Occurrence:
    match = PARSE_TIME_PATTERN.match(raw)
    if not match:
        raise InferenceFailed(f"unsupported time pattern: {raw!r}")

    hour = match.group("hour")
    min = match.group("min") or 0
    am_pm = match.group("am_pm")

    h = int(hour)
    m = int(min)
    match am_pm:
        case None | "am" | "AM":
            h += 0
        case "pm" | "PM":
            h += 12
        case _:
            raise UnexpectedScenario(f"expected AM/PM, but got {am_pm!r} instead")

    at = start_of_today(tz=tz) + datetime.timedelta(hours=h, minutes=m)

    return at


def _infer_start_with_at_x(raw: str, tz: datetime.timezone) -> tuple[str, Once]:
    """
    Return the Schedule for an utterance like 'at 8.32am ...'.
    """
    match = STARTS_WITH_AT.match(raw)
    if not match:
        raise InferenceFailed(f"expected to start with 'at <time_pattern>', but got {raw} instead")

    description = match.group("description")
    when = match.group("when")

    at = _infer_at_time(raw=when, tz=tz)
    return description, Once(at=at)


def _infer_ends_with_at_x(raw: str, tz: datetime.timezone) -> tuple[str, Once]:
    """
    Return the Schedule for an utterance like '... at 8.32am'.
    """

    match = ENDS_WITH_AT.match(raw)
    if not match:
        raise InferenceFailed(f"expected to end with 'at <time_pattern>', but got {raw} instead")

    description = match.group("description")
    when = match.group("when")

    at = _infer_at_time(raw=when, tz=tz)
    return description, Once(at=at)


def _infer_schedule(utterance: Utterance, tz: datetime.timezone) -> tuple[Description, Schedule]:
    """
    Takes human friendly texts and transforms them into something that can be scheduled

    The interpreter is timezone aware.
    """
    try:
        return _infer_starts_with_in_x_time(raw=utterance, tz=tz)
    except InferenceFailed:
        ...

    try:
        return _infer_ends_with_in_x_time(raw=utterance, tz=tz)
    except InferenceFailed:
        ...

    try:
        return _infer_start_with_at_x(raw=utterance, tz=tz)
    except InferenceFailed:
        ...

    try:
        return _infer_ends_with_at_x(raw=utterance, tz=tz)
    except InferenceFailed:
        ...

    raise InferenceFailed(f"Could not infer schedule from {utterance!r}")

    # yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
    # tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
    # return Schedule(
    #     starts_at=yesterday,
    #     interval="* * * * *",
    #     ends_at=tomorrow,
    # )


def infer_reminder(utterance: Utterance, tz: datetime.timezone) -> NewReminder:
    description, schedule = _infer_schedule(utterance=utterance, tz=tz)
    return NewReminder(description=description, schedule=schedule)


def infer_timezone(raw: IsoTimezone) -> datetime.timezone:
    clean = raw.strip()
    if clean == "Z":
        return datetime.timezone.utc

    match = TIMEZONE_PATTERN.match(clean)
    if not match:
        raise InferenceFailed(f"expected a timezone-like string (e.g. '+02:00'), but got {raw} instead")

    sign: Literal["+", "-"] = match.group("sign")  # type: ignore
    hours = int(match.group("hours"))
    mins = int(match.group("mins"))

    delta = datetime.timedelta(hours=hours, minutes=mins)

    match sign:
        case "+":
            delta = delta
        case "-":
            delta = -delta
        case _:
            raise InferenceFailed(f"expected '+' or '-', but got {sign!r} instead")

    tz = datetime.timezone(delta)
    return tz
