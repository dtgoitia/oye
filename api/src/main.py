"""
Adapters:
    API
        - webapp can add reminders, navigate them, get push notifications
        - Telegram/Slack can add reminders, navigate them, get push notifications
    CLI: CRUD reminders

Lifecycle manager: persists, reviews and notifies to the required adapters when needed
"""
from __future__ import annotations

import asyncio
import datetime
import enum
import heapq
import logging
import re
from dataclasses import dataclass
from typing import Callable, Iterator, Protocol, TypeAlias, assert_never

from src.config import Config
from src.model import ReminderId

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Reminder:
    """
    Represents a task/note that must be reminded (once/many times).

    A Reminder can have only one Schedule.
        - NOTE: if a Schedule is timezone sensitive (e.g.: every day at 9am), when a
          client changes timezones it must notify the API so that the API can update
          the Schedule. If the client allows scheduling offline reminders, then the
          client is responsible for dealing with the timezone changes.
    """

    id: ReminderId
    description: str
    schedule: Once  # add more types here: Once | Recurring

    @property
    def next_occurrence(self) -> Occurrence:
        return self.schedule.next_occurrence


class Schedule(Protocol):
    """
    Represents when a Reminder Notifications must be triggered, which could be once or
    multiple times. Each of those "times" is an _Occurrence_.

    TODO: perhaps https://pypi.org/project/python-crontab/ can model this for you
    """

    # starts_at: datetime.datetime
    # ends_at: datetime.datetime  # exclusive? inclusive?

    @property
    def next_occurrence(self) -> Occurrence:
        raise NotImplementedError(
            "using the definition of the schedule and the current time, calculate next ocurrence"
        )


@dataclass(frozen=True)
class Once(Schedule):
    """
    Represents a Schedule that only has one Occurrence.
    """

    _type = "once"

    at: datetime.datetime

    @property
    def next_occurrence(self) -> Occurrence:
        return self.at


@dataclass(frozen=True)
class Recurring(Schedule):
    """
    Represents a Schedule that has multiple Occurrences.
    """

    _type = "recurring"

    at: datetime.datetime

    @property
    def next_occurrence(self) -> Occurrence:
        return self.at


"""
Moment in which a user will get notified regarding a specific Reminder.
"""
Occurrence: TypeAlias = datetime.datetime


class Scheduler:
    """
    Responsible for holding the state of the queue, mappings, etc.
    """

    def add(self, reminder: Reminder) -> None:
        ...

    def replace(self, reminder: Reminder) -> None:
        """
        Update an existing reminder
        """
        # TODO: match by reminder.id
        ...

    def start(self) -> None:
        """
        Start regularly checking the reminders and notify when needed
        """
        # TODO: when a reminder must be notified --> `notify(reminder)`
        ...


ENDS_WITH_IN = re.compile(r".* in (?P<amount>[0-9]+)\s*(?P<unit>[a-zA-Z]+)$")


class InferenceFailed(Exception):
    ...


def get_now_utc() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


class AmountMustBeNumeric(Exception):
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


def _infer_in_x_time(raw: str) -> Once:
    """
    Return the Schedule for an utterance like 'in 3 mins'.
    """

    match = ENDS_WITH_IN.match(raw)
    if not match:
        raise InferenceFailed(f"expected to end with 'in X min', but got {raw} instead")

    amount = match.group("amount")
    unit = match.group("unit")

    return Once(at=get_now_utc() + _infer_delta(raw_amount=amount, raw_unit=unit))


def infer_schedule(raw: str) -> Schedule:
    """
    Takes human friendly texts and transforms them into something that can be scheduled

    The interpreter is timezone aware.
    """
    return _infer_in_x_time(raw=raw)

    # yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
    # tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
    # return Schedule(
    #     starts_at=yesterday,
    #     interval="* * * * *",
    #     ends_at=tomorrow,
    # )


Priority: TypeAlias = float
PrioritizedOcurrence: TypeAlias = tuple[Priority, Occurrence]


class UniqueHeapQueue:
    """
    Min-heap that only contains unique values.
    """

    def __init__(self) -> None:
        self.heap: list[PrioritizedOcurrence] = []

        # To track items in heap and avoid duplicates
        self._in_heap: set[Occurrence] = set()

    def __repr__(self) -> str:
        return "".join(
            [
                f"{UniqueHeapQueue.__name__}(",
                ", ".join(f"{x}" for x in self.heap),
                ")",
            ]
        )

    def add(self, occurrences: list[Occurrence]) -> None:
        """Adds many occurrences - duplicates are not added"""
        new_occurrences = list(set(occurrences) - self._in_heap)
        prioritized = [self._wrap(x) for x in new_occurrences]
        heapq.heapify(prioritized)
        self.heap = list(heapq.merge(self.heap, prioritized))
        self._in_heap.update(new_occurrences)

    def _wrap(self, occurrence: Occurrence) -> PrioritizedOcurrence:
        """Wrap the value in a tuple with a priority: `(priority, value)`"""
        return (occurrence.timestamp(), occurrence)

    def _unwrap(self, prioritized: PrioritizedOcurrence) -> Occurrence:
        """Unwrap the prioritized tuple and return only the value"""
        return prioritized[1]

    def peek_all(self) -> Iterator[Occurrence]:
        h = self.heap.copy()
        prioritized_occurrences = (heapq.heappop(h) for _ in range(len(h)))
        occurrences = map(self._unwrap, prioritized_occurrences)
        return occurrences

    def _pop(self) -> Occurrence:
        occurrence = self._unwrap(heapq.heappop(self.heap))
        self._in_heap.remove(occurrence)
        return occurrence

    def pop_occurrences(self, *, until: datetime.datetime) -> Iterator[Occurrence]:
        """
        Return every ocurrence until the provided `datetime.datetime` (excluded).
        """
        while True:
            try:
                occurrence = self._pop()
            except IndexError:
                return  # nothing else to return

            if occurrence >= until:
                self.add([occurrence])
                return

            yield occurrence


class ReminderRepository:
    def __init__(self) -> None:
        self._map: dict[ReminderId, Reminder] = {}

    def add(self, reminder: Reminder) -> None:
        if reminder.id in self._map:
            return
        self._map[reminder.id] = reminder

    def get_reminders_from(self, *, occurrences: Iterator[Occurrence]) -> Iterator[Reminder]:
        _map = self._reminders_by_next_occurrence()

        for occurrence in occurrences:
            try:
                # TODO: add test to ensure that the same occurrence in different
                # timezones behave as if they would be the same datetime
                reminders = _map[occurrence]
            except KeyError:
                continue

            yield from reminders

    def _reminders_by_next_occurrence(self) -> dict[Occurrence, list[Reminder]]:
        result: dict[Occurrence, list[Reminder]] = {}
        for reminder in self._map.values():
            occurrence = reminder.next_occurrence
            if occurrence in result:
                result[occurrence].append(reminder)
            else:
                result[occurrence] = [reminder]

        return result


NotifyCallback: TypeAlias = Callable[[Reminder], None]


class Engine:
    """
    Orchestrates all the components
    """

    def __init__(self, manager: ReminderRepository, notify_cb: NotifyCallback, config: Config) -> None:
        self._config = config
        self._man = manager
        self._notifier = notify_cb
        self._queue = UniqueHeapQueue()

        self._tick_delta = datetime.timedelta(seconds=config.engine_tick_delta)

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        self._last_tick = now - self._tick_delta

    def add_reminder(self, reminder: Reminder) -> None:
        logger.debug(f"adding reminder {reminder.id}")
        self._queue.add([reminder.next_occurrence])
        self._man.add(reminder)

    def get_reminders(self) -> Iterator[Reminder]:
        occurrences = self._queue.peek_all()
        reminders = self._man.get_reminders_from(occurrences=occurrences)
        yield from reminders

    def tick(self):
        """
        The engine processes next tick.
        """
        logger.debug("ticking: started")

        next_tick = self._compute_next_tick()
        logger.debug(f"ticking: next_tick:{next_tick}")
        next_occurrences = self._queue.pop_occurrences(until=next_tick)
        next_reminders = self._man.get_reminders_from(occurrences=next_occurrences)

        for reminder in next_reminders:
            self._notifier(reminder)

        logger.debug("ticking: completed")

    def _compute_next_tick(self) -> datetime.datetime:
        next_tick = self._last_tick + self._tick_delta
        self._last_tick = next_tick
        return next_tick

    def run(self) -> None:
        """
        Tick indefinitely.
        """
        logger.debug("running")

        async def _tick_indefinitely():
            logger.debug("ticking indefinitely")
            while True:
                self.tick()
                await asyncio.sleep(delay=self._config.engine_tick_delta)

        loop = asyncio.get_event_loop()
        task = loop.create_task(_tick_indefinitely())

        # TODO: think about how to stop this event loop gracefully
        loop.run_until_complete(task)


def notify_to_stdout(reminder: Reminder) -> None:
    """
    Depending on the user configurations and available clients, notify a message.
    """
    # TODO: mock notification to print in terminal
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    print(f"{now.isoformat()} - {reminder.description}")


def update_queue():
    """
    in a heapqueue, keep timestamps, which is the next timestamp to which you need to react
    on each tick:
        traverse heapqueue to get all items (`queued_times`) inside the time block
        queued_times: list[datetime.datetime]
        for t in queued_times:
            reminders: list[Reminder] = scheduled[t]
            for reminder in reminders:
                reminder.remind()

    queue contains timestamps:
    rationale: there might be multiple reminders in the same timestamp



    use case: modify/delete an existing reminder
        - find reminder
        - delete from queue -> removing from `scheduled` map is enough, if map has a key with an empty list, it's not a problem
        - keeping timestamps in queue
            - pro: easier to sort <--happens very often
            - con: harder to delete find by reminder id <-- happens less often than sorting

    use case: snooze a reminder
        - only needs to add the Reminder to the Scheduler with a new timestamp

    """  # noqa: E501
    ...


def on_tick() -> None:
    # Find in storage what needs to be notified in the next tick - blocks of 60s
    ...
