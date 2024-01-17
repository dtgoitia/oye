from dataclasses import replace

import pytest
from aiosqlite import Connection

from src import use_cases
from src.adapters.clients.db import insert_reminder, read_all_reminders
from src.domain.reminders import Once
from tests.factories import build_reminder
from tests.factories import d as _d


@pytest.mark.asyncio
async def test_calculate_next_occurrence_for_a_single_occurrence_reminder(
    db: Connection,
) -> None:
    """
    dispatch when: now <= next_occurrence AND dispatched IS FALSE
    """
    # Given
    now = _d("2024-01-20 00:00:00 +00:00")
    a = build_reminder(
        schedule=Once(at=_d("2024-01-17 00:00:01 +01:00")),
        next_occurrence=None,
        dispatched=True,
    )
    b = build_reminder(
        schedule=Once(at=_d("2024-01-17 00:00:02 +01:00")),
        next_occurrence=None,
        dispatched=False,
    )
    c = build_reminder(
        schedule=Once(at=_d("2024-01-17 00:00:03 +01:00")),
        next_occurrence=_d("2024-01-17 00:00:03 +01:00"),
        dispatched=True,
    )
    d = build_reminder(
        schedule=Once(at=_d("2024-01-25 00:00:00 +01:00")),
        next_occurrence=_d("2024-01-25 00:00:00 +01:00"),
        dispatched=False,
    )
    all_reminders = [
        a,
        b,
        c,
        d,
    ]
    for reminder in all_reminders:
        await insert_reminder(reminder=reminder, db=db)
    before = await read_all_reminders(db=db)
    assert before == all_reminders

    # When
    await use_cases.calculate_next_occurrences(db=db, now=now)

    # Then
    after = await read_all_reminders(db=db)
    assert after == [
        # a,  # deleted from db, as it wasn in an invalid state
        replace(b, next_occurrence=_d("2024-01-17 00:00:02 +01:00")),
        c,
        d,
    ]
