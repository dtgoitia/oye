import enum
from dataclasses import dataclass

from src.devex import todo
from src.model import JsonDict


class EventType(enum.Enum):
    tick = "tick"
    reminder_added = "reminder.added"
    reminder_updated = "reminder.updated"
    reminder_deleted = "reminder.deleted"


class UnsupportedEvent(Exception):
    ...


@dataclass(frozen=True)
class Event:
    type: EventType
    payload: JsonDict | None = None


async def update_in_memory_engine() -> None:
    todo()


async def handle(event: Event) -> None:
    match event.type:
        case EventType.tick:
            return print("handling a tick!")
        case EventType.reminder_added | EventType.reminder_updated | EventType.reminder_deleted:
            await update_in_memory_engine()
        case _:
            raise UnsupportedEvent(f"Event {event.type!r} is not supported")
