from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Protocol, TypeAlias

from src.model import ReminderId

"""
Moment in which a user will get notified regarding a specific Reminder.
"""
Occurrence: TypeAlias = datetime.datetime


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


@dataclass(frozen=True)
class NewReminder:
    description: str
    schedule: Once  # add more types here: Once | Recurring


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
