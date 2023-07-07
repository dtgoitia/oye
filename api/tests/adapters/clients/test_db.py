from dataclasses import replace
from typing import AsyncIterator

import aiosqlite
import pytest
import pytest_asyncio
from aiosqlite import Connection

from src.adapters.clients.db import (
    create_tables_if_needed,
    insert_reminder,
    read_all_reminders,
    upsert_reminder,
)
from src.config import Config
from src.domain.reminders import Once, Reminder
from tests.factories import d


@pytest_asyncio.fixture
async def db(config: Config) -> AsyncIterator[Connection]:
    async with aiosqlite.connect(database=config.db_uri) as db:
        await create_tables_if_needed(db=db)

        await db.execute("BEGIN;")

        yield db

        await db.rollback()


@pytest.mark.asyncio
async def test_insert_reminders(db: Connection) -> None:
    reminders = await read_all_reminders(db=db)
    assert reminders == []

    reminder_a = Reminder(
        id="rem_00000000",
        description="do foo",
        schedule=Once(at=d("2023-07-05 00:00:01 +01:00")),
    )
    reminder_b = Reminder(
        id="rem_11111111",
        description="do bar",
        schedule=Once(at=d("2023-07-05 00:00:13 +01:00")),
    )

    await insert_reminder(reminder=reminder_a, db=db)
    await insert_reminder(reminder=reminder_b, db=db)

    reminders = await read_all_reminders(db=db)
    assert reminders == [reminder_a, reminder_b]


@pytest.mark.asyncio
async def test_read_reminders(db: Connection) -> None:
    reminders = await read_all_reminders(db=db)
    assert reminders == []


@pytest.mark.asyncio
async def test_update_reminder(db: Connection) -> None:
    # Given a reminder
    reminder = Reminder(
        id="rem_00000000",
        description="do foo",
        schedule=Once(at=d("2023-07-05 00:00:01 +01:00")),
    )
    await insert_reminder(reminder=reminder, db=db)
    reminders = await read_all_reminders(db=db)
    assert reminders == [reminder]

    # when a reminder with the same ID upserted
    updated = replace(reminder, description="do bar")

    await upsert_reminder(updated, db=db)

    reminders = await read_all_reminders(db=db)
    assert reminders == [updated]
