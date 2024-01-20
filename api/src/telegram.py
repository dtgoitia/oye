from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TypeAlias

import aiosqlite

from src import use_cases
from src.adapters.api.telegram_bot import build_snooze_callback_data
from src.config import Config
from src.domain.ids import generate_id
from src.domain.reminders import Reminder
from telegram import Bot as TelegramBot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Message as TelegramMessage
from telegram.ext import Application, ApplicationBuilder

logger = logging.getLogger(__name__)


def build_application(config: Config) -> Application:
    application = ApplicationBuilder().token(config.telegram_api_token.value).build()
    return application


MessageId: TypeAlias = str


@dataclass(frozen=True)
class Message:
    id: MessageId
    telegram_message: TelegramMessage


def generate_message_id() -> MessageId:
    return generate_id(prefix="mess")


class Bot:
    def __init__(self, config: Config) -> None:
        self._config = config

        application = build_application(config=config)
        self._tbot: TelegramBot = application.bot

    async def send_reminder(self, reminder: Reminder) -> None:
        def _snooze(t: str) -> str:
            return build_snooze_callback_data(raw_time_utterance=t, reminder_id=reminder.id)

        chat_id = "-1001998360297"

        logger.debug(f"dispatching Telegram message for reminder {reminder.id} to chat {chat_id}")
        await self._tbot.send_message(
            # TODO: `chat_id` should be stored somehow in DB, but it feels that
            # the reminders table should not care about this kind of data, and
            # a Telegram-aware table should contain it instead. The same applies
            # to the data related to failed message deliveries to Telegram,
            # retries to Telegram, etc. - they all should live in a separate
            # place, this way you can replace Telegram with anything else easily
            chat_id=chat_id,
            text=reminder.description,
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

        logger.debug(f"marking reminder {reminder.id} as dispatched in DB")
        async with aiosqlite.connect(database=self._config.db_uri) as db:
            await use_cases.mark_reminder_as_dispatched(db=db, reminder=reminder)
