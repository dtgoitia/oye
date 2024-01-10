from dataclasses import replace

import pytest
from aiosqlite import Connection

from src.adapters.clients.db import (
    ReminderIdMustBeUnique,
    insert_reminder,
    read_all_reminders,
    upsert_reminder,
)
from src.domain.reminders import Once, Reminder
from tests.factories import d


@pytest.mark.asyncio
async def test_insert_reminders(db: Connection) -> None:
    reminders = await read_all_reminders(db=db)
    assert reminders == []

    reminder_a = Reminder(
        id="rem_00000000",
        description="do foo",
        schedule=Once(at=d("2023-07-05 00:00:01 +01:00")),
        dispatched=True,
    )
    reminder_b = Reminder(
        id="rem_11111111",
        description="do bar",
        schedule=Once(at=d("2023-07-05 00:00:13 +01:00")),
        dispatched=False,
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


@pytest.mark.asyncio
async def test_fail_if_same_reminder_is_inserted_twice(db: Connection) -> None:
    # Given a reminder
    reminder = Reminder(
        id="rem_00000000",
        description="do foo",
        schedule=Once(at=d("2023-07-05 00:00:01 +01:00")),
    )
    await insert_reminder(reminder=reminder, db=db)
    reminders = await read_all_reminders(db=db)
    assert reminders == [reminder]

    # when a reminder with the same ID is inserted (not upserted)
    with pytest.raises(ReminderIdMustBeUnique):
        await insert_reminder(reminder=reminder, db=db)
