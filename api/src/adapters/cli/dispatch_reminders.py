import asyncio
import logging
import os
from dataclasses import dataclass
from typing import TypeAlias

import aiosqlite
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Message as TelegramMessage
from telegram.ext import ApplicationBuilder

from src import use_cases
from src.adapters.api.telegram_bot import build_snooze_callback_data
from src.config import Config, get_config
from src.domain.ids import generate_id
from src.domain.reminders import Reminder
from src.logs import LOG_DATE_FORMAT, LOG_FORMAT

MessageId: TypeAlias = str

logger = logging.getLogger(__name__)


def generate_message_id() -> MessageId:
    return generate_id(prefix="mess")


@dataclass(frozen=True)
class Message:
    id: MessageId
    telegram_message: TelegramMessage


async def amain(config: Config) -> None:
    application = ApplicationBuilder().token(os.environ["TELEGRAM_API_TOKEN"]).build()
    bot: telegram.Bot = application.bot

    async def send_message(
        chat_id: str, message_id: MessageId, message: str, reply_markup: InlineKeyboardMarkup
    ) -> TelegramMessage:
        sent_message = await bot.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=reply_markup,
        )
        return Message(id=message_id, telegram_message=sent_message)

    async with aiosqlite.connect(database=config.db_uri) as db:
        reminders = await use_cases.get_reminders_to_dispatch(db=db)

    # we want to trace which messages belong to which reminder
    _map: dict[MessageId, Reminder] = {}

    tasks: list[asyncio.Task[Message]] = []

    logger.debug(f"sending {len(reminders)} messages")
    for reminder in reminders:
        message_id = generate_message_id()
        _map[message_id] = reminder

        def _snooze(t: str) -> str:
            return build_snooze_callback_data(raw_time_utterance=t, reminder_id=reminder.id)

        task = asyncio.create_task(
            send_message(
                # TODO: `chat_id` should be stored somehow in DB, but it feels that
                # the reminders table should not care about this kind of data, and
                # a Telegram-aware table should contain it instead. The same applies
                # to the data related to failed message deliveries to Telegram,
                # retries to Telegram, etc. - they all should live in a separate
                # place, this way you can replace Telegram with anything else easily
                chat_id="-1001998360297",
                message=reminder.description,
                message_id=message_id,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        #    [  1  ][  2  ]
                        #    [      3     ]
                        [
                            # https://core.telegram.org/bots/api#inlinekeyboardbutton
                            InlineKeyboardButton(text="1m", callback_data=_snooze("1m")),
                            InlineKeyboardButton(text="2m", callback_data=_snooze("2m")),
                            InlineKeyboardButton(text="3m", callback_data=_snooze("3m")),
                        ],
                        [
                            InlineKeyboardButton(text="10m", callback_data=_snooze("10m")),
                            InlineKeyboardButton(text="1h", callback_data=_snooze("1h")),
                            InlineKeyboardButton(text="1d", callback_data=_snooze("1d")),
                        ],
                    ],
                ),
            )
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    logger.debug("marking messages as dispatched")
    async with aiosqlite.connect(database=config.db_uri) as db:
        for message in results:
            reminder = _map[message.id]
            await use_cases.mark_reminder_as_dispatched(db=db, reminder=reminder)


def main() -> None:
    config = get_config()

    asyncio.run(amain(config=config))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    main()
