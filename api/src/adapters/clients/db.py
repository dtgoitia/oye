import datetime
import json
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


class Tables:
    reminders = Table(name="reminders", fields=["id", "updated_at", "reminder"])


async def create_table_if_needed(table: Table, db: Connection) -> None:
    query = f"CREATE TABLE IF NOT EXISTS {table.name}({ ', '.join(table.fields) });"
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
    await db.execute(sql=query, parameters=params)
