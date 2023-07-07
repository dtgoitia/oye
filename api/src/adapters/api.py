from apischema import serialize
from sanic import Request, Sanic
from sanic import exceptions as errors
from sanic.log import logger
from sanic.response import JSONResponse, json

from src import domain
from src.adapters.clients import nats
from src.config import get_config
from src.domain.inference import infer_reminder
from src.main import Engine

config = get_config()

api = Sanic.get_app(
    name=config.server_name,
    force_create=True,
)


class ApiRoutes:
    health = "/health"
    reminder = "/reminder"
    test_publish = "/pub"


# @api.reload_process_start
# async def before_api_starts(server_app: Sanic) -> None:
#     logger.debug("init: starting...")
#     engine = initialize_engine(config=config)
#     logger.debug("init: engine initialized")
#     server_app.ctx.engine = engine
#     logger.debug("init: engine attached to server")


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
async def create_reminder(request: Request) -> JSONResponse:
    utterance: str = request.json["utterance"]
    try:
        reminder = infer_reminder(utterance=utterance)
    except domain.inference.InferenceFailed as error:
        logger.debug(f"{error.__class__.__name__}: {error}")
        return errors.BadRequest("Could not understand utterance")

    engine: Engine = api.ctx.engine
    added = engine.create_reminder(reminder=reminder)
    return json({"added_reminder": serialize(added)})


if __name__ == "__main__":
    api.run(
        host=config.host,
        port=config.port,
        debug=config.debug_mode,
        auto_reload=config.debug_mode,
        access_log=True,
    )
