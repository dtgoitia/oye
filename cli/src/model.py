import datetime
from dataclasses import dataclass
from typing import Any, TypeAlias

JsonDict: TypeAlias = dict[str, Any]
Utterance: TypeAlias = str
ReminderId: TypeAlias = str


@dataclass(frozen=True)
class Once:
    _type = "once"
    at: datetime.datetime


@dataclass(frozen=True)
class Reminder:
    id: ReminderId
    description: str
    schedule: Once  # add more types here: Once | Recurring
