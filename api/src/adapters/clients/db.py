import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from textwrap import dedent
from typing import TypeAlias

import aiosqlite
from aiosqlite import Connection
from apischema import deserialize

from src.config import Config
from src.devex import UnexpectedScenario
from src.domain.reminders import Reminder
from src.model import ReminderId

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Table:
    name: str
    fields: list[str]
    primary_key_field: str


class Tables:
    reminders = Table(
        name="reminders",
        fields=["id", "description", "schedule", "next_occurrence", "dispatched"],
        primary_key_field="id",
    )


async def initialize(config: Config) -> None:
    logger.info("initializing database: start")
    async with aiosqlite.connect(database=config.db_uri) as db:
        await create_tables_if_needed(db=db)
    logger.info("initializing database: end")


async def create_tables_if_needed(db: Connection) -> None:
    await create_table_if_needed(table=Tables.reminders, db=db)


async def create_table_if_needed(table: Table, db: Connection) -> None:
    primary_key = table.primary_key_field
    other_fields = [field for field in table.fields if field != primary_key]
    query = dedent(
        f"""
        CREATE TABLE IF NOT EXISTS {table.name}(
            {primary_key} PRIMARY KEY,
            { ', '.join(other_fields) }
        );
        """
    ).strip()
    await db.execute(query)

    index_name = f"idx_{table.name}_id"
    query = f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {table.name}(id);"
    await db.execute(query)


def _row_to_reminder(row: sqlite3.Row) -> Reminder:
    as_dict = {
        **row,
        "schedule": json.loads(row["schedule"]),
        "dispatched": bool(row["dispatched"]),
    }
    reminder = deserialize(Reminder, as_dict)
    return reminder


async def read_all_reminders(db: Connection) -> list[Reminder]:
    table = Tables.reminders
    query = f"SELECT * FROM {table.name};"

    db.row_factory = aiosqlite.Row

    result = await db.execute(query)
    rows = list(await result.fetchall())

    return list(map(_row_to_reminder, rows))


class DataIntegrityError(Exception):
    ...


async def read_reminder(db: Connection, reminder_id: ReminderId) -> Reminder | None:
    table = Tables.reminders
    query = f"SELECT * FROM {table.name} WHERE id = :id;"

    db.row_factory = aiosqlite.Row

    result = await db.execute(query, {"id": reminder_id})
    rows = list(await result.fetchall())

    if not rows:
        return None

    if len(rows) > 1:
        raise DataIntegrityError(
            f"expected one Reminder with id {reminder_id!r}, but got {len(rows)} instead"
        )

    row = rows[0]

    reminder = _row_to_reminder(row=row)

    return reminder


async def read_reminders_from_db_to_dispatch(db: Connection) -> list[Reminder]:
    table = Tables.reminders
    query = dedent(
        f"""
        SELECT * FROM {table.name}
        WHERE dispatched IS FALSE
          AND next_occurrence IS NULL
          AND next_occurrence <= :now_utc
        ;
        """
    ).strip()
    print(query)

    db.row_factory = aiosqlite.Row

    result = await db.execute(query, {"now_utc": datetime.now(tz=timezone.utc)})
    rows = list(await result.fetchall())

    return list(map(_row_to_reminder, rows))


async def delete_reminder(db: Connection, reminder_id: ReminderId) -> Reminder | None:
    table = Tables.reminders

    reminder = await read_reminder(db=db, reminder_id=reminder_id)
    if not reminder:
        return None

    delete_query = f"DELETE FROM {table.name} WHERE id = ?;"
    # query = f"delete from reminders where id = '{reminder_id}' RETURNING id;"
    params: tuple[ReminderId] = (reminder_id,)

    await db.execute(delete_query, params)
    await db.commit()

    after_deletion = await read_reminder(db=db, reminder_id=reminder_id)
    if after_deletion is not None:
        raise UnexpectedScenario(
            f"expected to delete reminder {reminder_id!r} but it still present in the DB"
        )

    return reminder


SqliteParams: TypeAlias = tuple


class ReminderIdMustBeUnique(Exception):
    ...


async def insert_reminder(reminder: Reminder, db: Connection) -> None:
    table = Tables.reminders
    query = dedent(
        f"""
        INSERT INTO {table.name}({ ', '.join(table.fields) })
        VALUES ({ ', '.join([f':{field}' for field in table.fields]) })
        ;
        """
    ).strip()

    try:
        await db.execute(sql=query, parameters=reminder.to_db_dict())
        await db.commit()
    except sqlite3.IntegrityError:
        raise ReminderIdMustBeUnique(
            "cannot insert reminder because there already is a reminder with the same ID in the DB"
        )


async def upsert_reminder(reminder: Reminder, db: Connection) -> None:
    table = Tables.reminders

    updatable_fields = [f for f in table.fields if f != "id"]

    query = dedent(
        f"""
        INSERT INTO {table.name}({ ', '.join(table.fields) })
        VALUES ({ ', '.join([f':{field}' for field in table.fields]) })
        ON CONFLICT(id) DO UPDATE SET {', '.join([f'{field}=:{field}' for field in updatable_fields])}
        ;
        """
    ).strip()

    await db.execute(sql=query, parameters=reminder.to_db_dict())
