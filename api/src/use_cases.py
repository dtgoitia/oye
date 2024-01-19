import datetime
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
from src.domain.reminders import (
    NewReminder,
    Reminder,
    Scenario,
    calculate_next_occurrence,
    generate_reminder_id,
    identify_scenario,
)
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


async def update_reminder(updated: Reminder, db: Connection) -> None:
    await upsert_reminder(reminder=updated, db=db)


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


async def calculate_next_occurrences(db: Connection, now: datetime.datetime) -> None:
    logger.info("processing reminders: started")

    reminders = await get_reminders(db=db)
    logger.debug(f"{len(reminders)} reminders found")
    for reminder in reminders:
        _log_prefix = f"reminder {reminder.id}"
        logger.debug(f"{_log_prefix}: identifying scenario...")
        scenario = identify_scenario(reminder=reminder, now=now)
        logger.debug(f"{_log_prefix}: {scenario=}")

        if scenario == Scenario.dispatched_reminder:
            logger.debug(f"{_log_prefix}: nothing to do")
            continue

        if scenario == Scenario.awaiting_for_next_occurrence_to_be_calculated:
            logger.debug(f"{_log_prefix}: calculating next occurrence...")
            updated = calculate_next_occurrence(reminder=reminder)
            await upsert_reminder(reminder=updated, db=db)
            logger.debug(f"{_log_prefix}: reminder updated in DB")
            continue

        if scenario == Scenario.invalid_reminder:
            logger.debug(f"{_log_prefix}: deleting invalid reminder...")
            await delete_reminder(reminder_id=reminder.id, db=db)
            logger.debug(f"{_log_prefix}: invalid reminder deleted")
            continue

    logger.info("processing reminders: ended")


def snooze_until(reminder: Reminder, t: datetime.datetime) -> Reminder:
    """
    Push `next_occurrence` until a specific timestamp - as opposed to specifying
    a time delta from now, where "now" is the instant when the user requests the
    snooze.

    """
    # TODO: if the reminder is recurring, you need to decide how to handle
    # conflicts between the `next_occurrence` as per the snooze and the schedule
    return replace(reminder, next_occurrence=t, dispatched=False)


# def snooze_for(reminder: Reminder, delta: datetime.timedelta):
#     """
#     Push `next_occurrence` for some minutes, seconds, etc. - as opposed to
#     specifying a specific timestamp.
#     """
#     # TODO: if the reminder is recurring, you need to decide how to handle
#     # conflicts between the `next_occurrence` as per the snooze and the schedule
#     raise NotImplementedError()
