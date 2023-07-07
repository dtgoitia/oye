import pytest

from src.devex import todo
from src.domain.event_handling import Event, EventType, handle


@pytest.mark.asyncio
@pytest.mark.skip(reason="TODO")
async def test_on_tick_load_reminders_from_db() -> None:
    # Given the engine has no reminders
    # TODO - engine assertion

    # and a reminder is added
    # TODO - add reminder to DB

    # when a tick event arrives
    await handle(event=Event(type=EventType.tick))

    # then the engine has all the reminders
    # TODO - engine assertion
    todo()
