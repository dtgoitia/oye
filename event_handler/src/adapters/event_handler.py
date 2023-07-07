import asyncio
import logging

from src.adapters import nats
from src.config import Config, get_config
from src.domain import event_handling
from src.domain.ticker import tick

logger = logging.getLogger(__name__)


async def _consume_nats_messages(config: Config) -> None:
    logger.info("Consuming NATS messages...")
    reminders_sub = await nats.get_subscription(subject="reminder.*", config=config)

    while True:
        logger.info("consume nats loop")
        try:
            msg = await reminders_sub.next_msg(timeout=None)
            event = nats.message_to_event(message=msg)
            await event_handling.handle(event)

        except nats.FailedToParseMessage as e:
            logger.error(e)

        except event_handling.UnsupportedEvent as e:
            logger.error(e)

        except Exception as e:
            _type = e.__class__.__name__
            message = str(e)
            logger.error(f"Unexpected error while processing msg={msg}: {_type}: {message}")


async def amain() -> None:
    logger.info("Event handler started")

    config = get_config()

    try:
        # start listening NATS messages
        asyncio.create_task(_consume_nats_messages(config=config))

        # kick-off ticker
        ticker = asyncio.create_task(tick(config=config))

        # Await one of the inifite tasks (I could have awaited the one that
        # consumes NATS messages) to avoid main function existing
        await ticker

    except KeyboardInterrupt:
        logger.info("Event handler interrupted via `KeyboardInterrupt`")

    logger.info("Event handler ended gracefully")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    asyncio.run(amain())
