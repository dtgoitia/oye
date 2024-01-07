import asyncio
import datetime
import logging
import os
from pprint import pprint

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

from src.config import get_config

WAIT_TO_DELETE_SNOOZED_REMINDER = 4  # seconds


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    print(f"\n\n{chat_id=}\n\n")


async def snooze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    previous_message = update.callback_query.message
    query = update.callback_query.data
    print(f"\n{query=}\n")

    # TODO: update next_ocurrence in DB
    next_occurrence = datetime.datetime.now(tz=datetime.timezone.utc)
    pprint(update.to_dict())

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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
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
