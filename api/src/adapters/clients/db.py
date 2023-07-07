import datetime
import json
import sqlite3
from dataclasses import dataclass
from textwrap import dedent
from typing import TypeAlias

from aiosqlite import Connection
from apischema import deserialize, serialize

from src.domain.reminders import Reminder


@dataclass(frozen=True)
class Table:
    name: str
    fields: list[str]
    primary_key_field: str


class Tables:
    reminders = Table(
        name="reminders",
        fields=["id", "updated_at", "reminder"],
        primary_key_field="id",
    )


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
    query = f"CREATE UNIQUE INDEX {index_name} ON {table.name}(id);"
    await db.execute(query)


async def create_tables_if_needed(db: Connection) -> None:
    await create_table_if_needed(table=Tables.reminders, db=db)


async def read_all_reminders(db: Connection) -> list[Reminder]:
    table = Tables.reminders
    query = f"SELECT * FROM {table.name};"

    result = await db.execute(query)
    rows = list(await result.fetchall())

    reminders: list[Reminder] = []
    for row in rows:
        __, _, json_str = row
        json_dict = json.loads(json_str)
        reminder = deserialize(Reminder, json_dict)
        reminders.append(reminder)

    return reminders


SqliteParams: TypeAlias = tuple


class ReminderIdMustBeUnique(Exception):
    ...


async def insert_reminder(reminder: Reminder, db: Connection) -> None:
    table = Tables.reminders
    query = dedent(
        f"""
        INSERT INTO {table.name}({ ', '.join(table.fields) })
        VALUES ({ ', '.join(['?' for _ in table.fields]) })
        ;
        """
    ).strip()

    now = datetime.datetime.now().isoformat()

    json_dict = serialize(reminder)
    json_str = json.dumps(json_dict)

    params = (reminder.id, now, json_str)
    try:
        await db.execute(sql=query, parameters=params)
    except sqlite3.IntegrityError:
        raise ReminderIdMustBeUnique(
            "cannot insert reminder because there already is a reminder with the same ID in the DB"
        )


async def upsert_reminder(reminder: Reminder, db: Connection) -> None:
    table = Tables.reminders
    query = dedent(
        f"""
        INSERT INTO {table.name}({ ', '.join(table.fields) })
        VALUES ({ ', '.join(['?' for _ in table.fields]) })
        ON CONFLICT(id) DO UPDATE SET
            updated_at=?,
            reminder=?
        ;
        """
    ).strip()

    now = datetime.datetime.now().isoformat()

    json_dict = serialize(reminder)
    json_str = json.dumps(json_dict)

    params = (reminder.id, now, json_str, now, json_str)
    await db.execute(sql=query, parameters=params)
