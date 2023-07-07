import json

import nats
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription

from src.config import Config
from src.domain.event_handling import Event, EventType


async def get_subscription(subject: str, config: Config) -> Subscription:
    servers: list[str] = [config.nats_url]

    nats_client = await nats.connect(servers=servers)
    sub = await nats_client.subscribe(subject=subject)
    return sub


class FailedToParseMessage(Exception):
    ...


def message_to_event(message: Msg) -> Event:
    try:
        _type = EventType(message.subject)
    except ValueError:
        raise FailedToParseMessage(f"message subject {message.subject!r} is not supported")

    try:
        payload = json.loads(message.data)
    except json.decoder.JSONDecodeError:
        raise FailedToParseMessage("message payload must be valid JSON")

    return Event(type=_type, payload=payload)
