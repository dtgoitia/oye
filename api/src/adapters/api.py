import asyncio
import logging

import aiosqlite
from apischema import serialize
from sanic import Request, Sanic
from sanic import exceptions as errors
from sanic.log import logger
from sanic.response import JSONResponse, json
from sanic_ext import openapi

from src import domain, use_cases
from src.adapters.clients import db, nats
from src.config import get_config
from src.domain.inference import infer_reminder
from src.model import ReminderId, Utterance

api = Sanic.get_app(name="oye-api", force_create=True)


class ApiRoutes:
    health = "/health"
    reminders = "/reminder"
    reminder = "/reminder/<reminder_id>"
    test_publish = "/pub"


@api.get(ApiRoutes.health)
async def health(_: Request) -> JSONResponse:
    return json({"health": True})


@api.get(ApiRoutes.test_publish)
async def test_publish(_: Request) -> JSONResponse:
    await nats.publish("boo")
    return json({"published": True})


@api.get(ApiRoutes.reminder)
async def get_reminder(_: Request, reminder_id: ReminderId) -> JSONResponse:
    config = get_config()

    async with aiosqlite.connect(database=config.db_uri) as db:
        reminder = await use_cases.get_reminder(db=db, reminder_id=reminder_id)
        if not reminder:
            raise errors.NotFound(f"no reminder found with ID {reminder_id!r}")
        return json({"reminder": serialize(reminder)})


@api.get(ApiRoutes.reminders)
async def get_all_reminders(_: Request) -> JSONResponse:
    config = get_config()

    async with aiosqlite.connect(database=config.db_uri) as db:
        reminders = await use_cases.get_reminders(db=db)
        return json({"reminders": serialize(reminders)})


@api.post(ApiRoutes.reminders)
@openapi.body({"utterance": Utterance})
async def create_reminder(request: Request) -> JSONResponse:
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


@api.delete(ApiRoutes.reminder)
async def delete_reminder(_: Request, reminder_id: ReminderId) -> JSONResponse:
    config = get_config()

    async with aiosqlite.connect(database=config.db_uri) as db:
        deleted = await use_cases.delete_reminder(db=db, reminder_id=reminder_id)

        if not deleted:
            raise errors.NotFound(f"nothing was deleted as no reminder was found with ID {reminder_id!r}")

        return json({"deleted_reminder": serialize(deleted)})


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
