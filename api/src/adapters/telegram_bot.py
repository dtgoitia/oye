import datetime
import logging
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

from src.config import get_config


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    print(f"\n\n{chat_id=}\n\n")


async def snooze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    query = update.callback_query.data
    print(f"\n{query=}\n")

    # TODO: update next_ocurrence in DB
    next_occurrence = datetime.datetime.now(tz=datetime.timezone.utc)

    # TODO: edit previous message and remove buttons
    await context.bot.send_message(chat_id=chat_id, text=f"snoozed until {next_occurrence}")


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
