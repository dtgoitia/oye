import asyncio
import enum
import json
import logging
from dataclasses import dataclass
from typing import TypeAlias

import nats
from nats.aio.msg import Msg

from src.config import get_config
from src.devex import todo
from src.model import JsonDict

logger = logging.getLogger(__name__)

EventId: TypeAlias = str


class EventType(enum.Enum):
    notify = "notify"
    reminder_added = "reminder.added"
    reminder_updated = "reminder.updated"
    reminder_deleted = "reminder.deleted"
    test = "greet.joe"


@dataclass(frozen=True)
class Event:
    id: EventId
    type: EventType
    payload: JsonDict | None = None


class UnsupportedEvent(Exception):
    ...


class FailedToParseMessage(Exception):
    ...


def nats_message_to_event(message: Msg) -> Event:
    try:
        _type = EventType(message.subject)
    except ValueError:
        raise FailedToParseMessage(f"message subject {message.subject!r} is not supported")

    try:
        payload = json.loads(message.data)
    except json.decoder.JSONDecodeError:
        raise FailedToParseMessage("message payload must be valid JSON")

    return Event(id="todo", type=_type, payload=payload)


async def update_in_memory_engine() -> None:
    todo()


async def handle_event(event: Event) -> None:
    match event.type:
        case EventType.test:
            print(f"Received test event: {event}")
        case EventType.reminder_added | EventType.reminder_updated | EventType.reminder_deleted:
            await update_in_memory_engine()
        case _:
            raise UnsupportedEvent(f"Event {event.type!r} is not supported")


async def amain() -> None:
    logger.info("Event handler started")

    config = get_config()

    servers: list[str] = [config.nats_url]

    nats_client = await nats.connect(servers=servers)
    sub = await nats_client.subscribe(subject="greet.*")

    while True:
        try:
            msg = await sub.next_msg(timeout=None)
            print(f"{msg.data} on subject {msg.subject}")
            event = nats_message_to_event(message=msg)
            await handle_event(event=event)
        except FailedToParseMessage as error:
            logger.error(error)
        except KeyboardInterrupt:
            logger.info("Event handler interrupted via `KeyboardInterrupt`")
            break

    logger.info("Event handler ended gracefully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    asyncio.run(amain())
