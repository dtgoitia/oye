import asyncio
import logging

from src.config import Config
from src.domain import event_handling
from src.domain.event_handling import Event, EventType

logger = logging.getLogger(__name__)


async def tick(config: Config) -> None:
    logger.info(f"Ticking every {config.tick_interval} seconds...")
    event = Event(type=EventType.tick, payload=None)

    while True:
        logger.debug("tick")
        await event_handling.handle(event)
        await asyncio.sleep(delay=config.tick_interval)
