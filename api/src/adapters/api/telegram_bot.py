import asyncio
import datetime
import logging
import os
import re
from typing import TypeAlias

import aiosqlite
from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

from src import use_cases
from src.config import get_config
from src.domain.inference import InferenceFailed, _infer_starts_with_in_x_time
from src.domain.reminders import Once, ReminderRepository
from src.logs import LOG_DATE_FORMAT, LOG_FORMAT
from src.model import ReminderId
from src.safety import Err, Ok, Result

logger = logging.getLogger(__name__)

WAIT_TO_DELETE_SNOOZED_REMINDER = 4  # seconds


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    print(f"\n\n{chat_id=}\n\n")


class InvalidQuery(Exception):
    ...


_SNOOZE_CALLBACK_DATA_PREFIX: str = "snooze:"
SNOOZE_CALLBACK_DATA_PATTERN = re.compile(
    rf"^{_SNOOZE_CALLBACK_DATA_PREFIX}"
    rf":(?P<when>.*)"
    rf":(?P<reminder_id>{ReminderRepository._reminder_id_prefix}_.*)"
)
CallbackData: TypeAlias = str


def build_snooze_callback_data(raw_time_utterance: str, reminder_id: ReminderId) -> CallbackData:
    return f"{_SNOOZE_CALLBACK_DATA_PREFIX}:{raw_time_utterance}:{reminder_id}"


def infer_next_occurrence_from_callback_data(
    data: str,
) -> Result[tuple[ReminderId, datetime.datetime], InvalidQuery | InferenceFailed]:
    if not data.startswith(_SNOOZE_CALLBACK_DATA_PREFIX):
        return Err(
            InvalidQuery(
                f"expected callback data to start with {_SNOOZE_CALLBACK_DATA_PREFIX!r}"
                f" but got this instead: {data!r}"
            )
        )
    match = SNOOZE_CALLBACK_DATA_PATTERN.match(data)
    if not match:
        return Err(
            InvalidQuery(
                f"expected callback data ({data!r}) to match this regex expression"
                f" {SNOOZE_CALLBACK_DATA_PATTERN.pattern!r}, but got this instead:"
                f" {data!r}"
            )
        )

    when = match.group("when")
    reminder_id = match.group("reminder_id")

    # ==========================================================================
    # HACK: the logic to infer a reminder (at the moment) the utterance must
    # have a description, so I'm patching myself the utterance to include a
    # description. The inferred description will be ignored.
    patch = "HACK_DESCRIPTION_TO_INFER_SCHEDULE"
    patched_raw = f"in {when} {patch}"

    try:
        description, schedule = _infer_starts_with_in_x_time(
            raw=patched_raw,
            tz=datetime.timezone.utc,
        )
    except InferenceFailed as error:
        return Err(error)

    if description != patch:
        raise NotImplementedError(
            f"expected inferred description ({description!r}) to match the patch ({patch!r})"
        )
    if not isinstance(schedule, Once):
        raise NotImplementedError(
            f"expected inferred schedule to be of {Once} type, but instead got"
            f" {schedule=}. Inferred from {data=}"
        )
    # ==========================================================================
    next_occurrence = schedule.next_occurrence

    return Ok((reminder_id, next_occurrence))


async def snooze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config = get_config()

    chat_id = update.effective_chat.id
    previous_message = update.callback_query.message
    data = update.callback_query.data

    match infer_next_occurrence_from_callback_data(data=data):
        case Ok(v):
            reminder_id, next_occurrence = v
        case Err(error):
            logger.error(f"failed to snooze {update=}, reason: {error}")
            return

    async with aiosqlite.connect(database=config.db_uri) as db:
        reminder = await use_cases.get_reminder(reminder_id=reminder_id, db=db)
        if not reminder:
            raise NotImplementedError(f"expected to find a reminder with id {reminder_id!r} but found none")
        updated = use_cases.snooze_until(reminder=reminder, t=next_occurrence)
        await use_cases.update_reminder(updated=updated, db=db)

    # mark message as snoozed
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=previous_message.id,
        text=f"{previous_message.text}\n\nsnoozed until {next_occurrence}",
        reply_markup=None,  # remove buttons
    )

    await asyncio.sleep(WAIT_TO_DELETE_SNOOZED_REMINDER)
    await context.bot.delete_message(chat_id=chat_id, message_id=previous_message.id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    config = get_config()

    application = ApplicationBuilder().token(os.environ["TELEGRAM_API_TOKEN"]).build()

    application.add_handler(CommandHandler(command="start", callback=start))
    application.add_handler(
        CallbackQueryHandler(
            callback=snooze,
            pattern="snooze:.*",  # used as ReGex to match incoming `callback_data`
        )
    )

    application.run_polling()
