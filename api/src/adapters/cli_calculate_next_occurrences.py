import asyncio
import datetime
import logging

import aiosqlite

from src import use_cases
from src.config import Config, get_config


async def amain(config: Config) -> None:
    async with aiosqlite.connect(database=config.db_uri) as db:
        await use_cases.calculate_next_occurrences(
            db=db,
            now=datetime.datetime.now(tz=datetime.timezone.utc),
        )


def main() -> None:
    config = get_config()

    asyncio.run(amain(config=config))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
