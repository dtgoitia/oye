import asyncio
import logging
from typing import TypeAlias

import aiosqlite

from src import telegram, use_cases
from src.config import Config, get_config
from src.logs import LOG_DATE_FORMAT, LOG_FORMAT

MessageId: TypeAlias = str

logger = logging.getLogger(__name__)


async def amain(config: Config) -> None:
    async with aiosqlite.connect(database=config.db_uri) as db:
        reminders = await use_cases.get_reminders_to_dispatch(db=db)

    logger.debug(f"sending {len(reminders)} messages")

    bot = telegram.Bot(config=config)
    tasks: list[asyncio.Task[None]] = [
        asyncio.create_task(bot.send_reminder(reminder)) for reminder in reminders
    ]

    await asyncio.gather(*tasks)


def main() -> None:
    config = get_config()

    asyncio.run(amain(config=config))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    main()
