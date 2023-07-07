import asyncio
import datetime

from src.adapters.clients.oye import OyeClient
from src.config import get_config
from src.domain.reminders import Once
from src.main import Reminder


async def amain() -> None:
    config = get_config()

    async with OyeClient(config=config) as oye:
        reminders = await oye.get_reminders()

        for i, reminder in enumerate(reminders):
            print(i, reminder)

        print("--------")

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        later = now + datetime.timedelta(seconds=2)
        reminder = Reminder(
            id="id_new_reminder",
            description="gooo!!",
            schedule=Once(at=later),
        )

        await oye.add_reminder(reminder=reminder)

        reminders = await oye.get_reminders()

        for i, reminder in enumerate(reminders):
            print(i, reminder)


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
