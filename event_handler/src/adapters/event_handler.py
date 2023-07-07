import asyncio
import logging

from src.adapters import nats
from src.config import get_config
from src.domain import event_handling

logger = logging.getLogger(__name__)


async def amain() -> None:
    logger.info("Event handler started")

    config = get_config()

    reminders_sub = await nats.get_subscription(subject="reminder.*", config=config)

    while True:
        try:
            msg = await reminders_sub.next_msg(timeout=None)
            event = nats.message_to_event(message=msg)
            await event_handling.handle(event)

        except nats.FailedToParseMessage as error:
            logger.error(error)

        except event_handling.UnsupportedEvent as error:
            logger.error(error)

        except KeyboardInterrupt:
            logger.info("Event handler interrupted via `KeyboardInterrupt`")
            break

    logger.info("Event handler ended gracefully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    asyncio.run(amain())
