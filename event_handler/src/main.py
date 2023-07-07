import asyncio

import nats

from src.config import get_config

# import os
# os.environ["NATS_URL"] = "nats://localhost:4222"


async def amain() -> None:
    config = get_config()
    print("foo")

    servers: list[str] = [config.nats_url]

    nats_client = await nats.connect(servers=servers)
    sub = await nats_client.subscribe(subject="greet.*")

    counter = 0
    while True:
        msg = await sub.next_msg(timeout=None)
        print(f"{msg.data} on subject {msg.subject}")
        counter += 1
        if counter == 3:
            break

    print("end")


if __name__ == "__main__":
    asyncio.run(amain())
