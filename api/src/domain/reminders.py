from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Iterator, Protocol, TypeAlias

from src.domain.ids import generate_id
from src.model import JsonDict, ReminderId

"""
Moment in which a user will get notified regarding a specific Reminder.
"""
Occurrence: TypeAlias = datetime.datetime


class Schedulable(Protocol):
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

    def to_json(self) -> JsonDict:
        raise NotImplementedError("provide a valid JSON representation")


@dataclass(frozen=True)
class Once(Schedulable):
    """
    Represents a Schedule that only has one Occurrence.
    """

    _type = "once"

    at: datetime.datetime

    @property
    def next_occurrence(self) -> Occurrence:
        return self.at

    def to_json(self) -> JsonDict:
        return {"at": self.at.isoformat()}


@dataclass(frozen=True)
class Recurring(Schedulable):
    """
    Represents a Schedule that has multiple Occurrences.
    """

    _type = "recurring"

    at: datetime.datetime

    @property
    def next_occurrence(self) -> Occurrence:
        return self.at


Schedule: TypeAlias = Once  # add more types here: Once | Recurring


@dataclass(frozen=True)
class NewReminder:
    description: str
    schedule: Schedule

    def to_json(self) -> JsonDict:
        return {"description": self.description, "schedule": self.schedule.to_json()}

    def to_reminder(self, id: ReminderId) -> Reminder:
        return Reminder(id=id, description=self.description, schedule=self.schedule)


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

    def to_json(self) -> JsonDict:
        return {"id": self.id, "description": self.description, "schedule": self.schedule.to_json()}


def generate_reminder_id() -> ReminderId:
    return generate_id(prefix=ReminderRepository._reminder_id_prefix)


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
