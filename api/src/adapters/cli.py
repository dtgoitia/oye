import asyncio
import os

from src.adapters.clients.oye import OyeClient
from src.config import get_config

os.environ["OYE_API_HOST"] = "localhost"


async def amain() -> None:
    config = get_config()

    async with OyeClient(config=config) as oye:
        # reminders = await oye.get_reminders()

        # for i, reminder in enumerate(reminders):
        #     print(i, reminder)

        # print("--------")

        await oye.add_reminder(utterance="do foo in 5 mins")

        # reminders = await oye.get_reminders()

        # for i, reminder in enumerate(reminders):
        #     print(i, reminder)


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
