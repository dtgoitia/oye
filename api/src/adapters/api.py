import asyncio
import logging

import aiosqlite
from apischema import serialize
from sanic import Request, Sanic
from sanic import exceptions as errors
from sanic.log import logger
from sanic.response import JSONResponse, json

from src import domain, use_cases
from src.adapters.clients import db, nats
from src.config import get_config
from src.domain.inference import infer_reminder
from src.main import Engine

api = Sanic.get_app(name="oye-api", force_create=True)


class ApiRoutes:
    health = "/health"
    reminder = "/reminder"
    test_publish = "/pub"


@api.get(ApiRoutes.health)
async def health(_: Request) -> JSONResponse:
    return json({"health": True})


@api.get(ApiRoutes.test_publish)
async def test_publish(_: Request) -> JSONResponse:
    await nats.publish("boo")
    return json({"published": True})


@api.get(ApiRoutes.reminder)
async def get_all_reminders(_: Request) -> JSONResponse:
    engine: Engine = api.ctx.engine
    reminders = list(engine.get_reminders())
    return json({"reminders": serialize(reminders)})


@api.post(ApiRoutes.reminder)
async def create_reminder(request: Request) -> JSONResponse | errors.BadRequest:
    config = get_config()

    try:
        utterance: str = request.json["utterance"]
    except (AttributeError, TypeError, KeyError):
        raise errors.BadRequest('Expected a payload like this: {"utterance":"foo"}')

    try:
        new_reminder = infer_reminder(utterance=utterance)
    except domain.inference.InferenceFailed as error:
        logger.debug(f"{error.__class__.__name__}: {error}")
        raise errors.BadRequest("Could not understand utterance")

    async with aiosqlite.connect(database=config.db_uri) as db:
        added = await use_cases.create_reminder(new_reminder, db=db)

    return json({"added_reminder": serialize(added)})


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    config = get_config()

    asyncio.run(db.initialize(config=config))

    api.run(
        host=config.host,
        port=config.port,
        debug=config.debug_mode,
        auto_reload=config.debug_mode,
        access_log=True,
    )
