from apischema import deserialize, serialize
from sanic import Request, Sanic
from sanic.log import logger
from sanic.response import JSONResponse, json

from src.config import get_config
from src.domain.use_cases import initialize_engine
from src.main import Engine, Reminder

config = get_config()

api = Sanic.get_app(
    name=config.server_name,
    force_create=True,
)


class ApiRoutes:
    health = "/health"
    reminder = "/reminder"


@api.before_server_start
async def before_server_starts(server_app: Sanic) -> None:
    logger.debug("init: starting...")
    engine = initialize_engine(config=config)
    logger.debug("init: engine initialized")
    server_app.ctx.engine = engine
    logger.debug("init: engine attached to server")


@api.get(ApiRoutes.health)
async def health(_: Request) -> JSONResponse:
    return json({"health": True})


@api.get(ApiRoutes.reminder)
async def get_all_reminders(_: Request) -> JSONResponse:
    engine: Engine = api.ctx.engine
    reminders = list(engine.get_reminders())
    return json({"reminders": serialize(reminders)})


@api.post(ApiRoutes.reminder)
async def create_reminder(request: Request) -> JSONResponse:
    reminder = deserialize(Reminder, request.json)
    engine: Engine = api.ctx.engine
    engine.add_reminder(reminder=reminder)
    added = reminder
    return json({"added_reminder": serialize(added)})


if __name__ == "__main__":
    api.run(
        host=config.host,
        port=config.port,
        debug=config.debug_mode,
        auto_reload=config.debug_mode,
        access_log=True,
    )
