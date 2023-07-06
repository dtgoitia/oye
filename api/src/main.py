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
import heapq
import logging
from typing import Callable, Iterator, TypeAlias

from src.config import Config
from src.domain.ids import generate_id
from src.domain.reminders import NewReminder, Occurrence, Reminder
from src.model import ReminderId

logger = logging.getLogger(__name__)


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
    _reminder_id_prefix = "rem"

    def __init__(self) -> None:
        self._map: dict[ReminderId, Reminder] = {}

    def _generate_reminder_id(self) -> ReminderId:
        while True:
            _id = generate_id(prefix=self._reminder_id_prefix)
            if _id not in self._map:
                return _id

    def add(self, new_reminder: NewReminder | Reminder) -> Reminder:
        if isinstance(new_reminder, NewReminder):
            reminder = Reminder(
                id=self._generate_reminder_id(),
                description=new_reminder.description,
                schedule=new_reminder.schedule,
            )
        else:
            reminder = new_reminder
        self._map[reminder.id] = reminder
        return reminder

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

    def create_reminder(self, reminder: NewReminder) -> Reminder:
        logger.debug("creating reminder")
        if isinstance(reminder, Reminder):
            print(f">>> adding {reminder}")
        else:
            breakpoint()
        added = self._man.add(reminder)
        self._queue.add([added.next_occurrence])
        return added

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
