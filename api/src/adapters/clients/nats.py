import os

import nats

# TODO: move to config
servers = os.environ.get("NATS_URL", "nats://localhost:4222").split(",")


async def publish(message: str) -> None:
    print(f">>>> {message}")
    nc = await nats.connect(servers=servers)

    await nc.publish("greet.joe", message.encode("utf-8"))
