import logging

from aiosqlite import Connection

from src.adapters.clients.db import ReminderIdMustBeUnique, insert_reminder
from src.devex import UnexpectedScenario
from src.domain.reminders import NewReminder, Reminder, generate_reminder_id

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
            await insert_reminder(reminder, db=db)
            break
        except ReminderIdMustBeUnique:
            # Just generate a new ID and retry
            reminder = None
            failures += 1
        except Exception as error:
            reminder = None
            logger.debug(f"{error.__class__.__name__}: {str(error)}")
            failures += 1

        if failures == retry_limit:
            raise UnexpectedScenario(
                f"failed to create a reminder {retry_limit} times, odd inspect logs: {new_reminder=}"
            )

    if reminder is None:
        raise UnexpectedScenario("expected reminder to be not None")

    return reminder
