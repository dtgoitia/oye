import logging
from dataclasses import replace

from aiosqlite import Connection

from src.adapters.clients.db import ReminderIdMustBeUnique
from src.adapters.clients.db import delete_reminder as delete_reminder_from_db
from src.adapters.clients.db import insert_reminder as insert_reminder_in_db
from src.adapters.clients.db import read_all_reminders as read_all_reminders_from_db
from src.adapters.clients.db import read_reminder as read_reminder_from_db
from src.adapters.clients.db import read_reminders_from_db_to_dispatch, upsert_reminder
from src.devex import UnexpectedScenario
from src.domain.reminders import NewReminder, Reminder, generate_reminder_id
from src.model import ReminderId

logger = logging.getLogger(__name__)


async def create_reminder(new_reminder: NewReminder, db: Connection) -> Reminder:
    retry_limit = 10
    reminder: Reminder | None = None

    # Try until all conditions are met
    failures = 0
    while True:
        try:
            # In the rare case of a collision of IDs, the DB will raise
            reminder_id = generate_reminder_id()
            reminder = new_reminder.to_reminder(id=reminder_id)
            await insert_reminder_in_db(reminder, db=db)
            break
        except ReminderIdMustBeUnique:
            # Just generate a new ID and retry
            reminder = None
            failures += 1
        except Exception as error:
            reminder = None
            logger.error(f"{error.__class__.__name__}: {str(error)}")
            failures += 1

        if failures == retry_limit:
            raise UnexpectedScenario(
                f"failed to create a reminder {retry_limit} times, odd inspect logs: {new_reminder=}"
            )

    if reminder is None:
        raise UnexpectedScenario("expected reminder to be not None")

    return reminder


async def get_reminders(db: Connection) -> list[Reminder]:
    reminders = await read_all_reminders_from_db(db=db)
    return reminders


async def get_reminder(reminder_id: ReminderId, db: Connection) -> Reminder | None:
    reminders = await read_reminder_from_db(reminder_id=reminder_id, db=db)
    return reminders


async def get_reminders_to_dispatch(db: Connection) -> list[Reminder]:
    reminders = await read_reminders_from_db_to_dispatch(db=db)
    return reminders


async def mark_reminder_as_dispatched(db: Connection, reminder: Reminder) -> None:
    logger.info(f"marking reminder {reminder.id} as dispatched")
    updated = replace(reminder, dispatched=True)
    await upsert_reminder(reminder=updated, db=db)


async def delete_reminder(reminder_id: ReminderId, db: Connection) -> Reminder | None:
    deleted = await delete_reminder_from_db(reminder_id=reminder_id, db=db)
    return deleted
