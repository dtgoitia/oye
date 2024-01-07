import logging
import os

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

from src.config import get_config


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print(f"\n\n{chat_id=}\n\n")
    # await context.bot.send_message(chat_id=chat_id, text="foo")
    # await context.bot.send_message(chat_id=chat_id, text="I'm a bot, please talk to me!")


# async def send_message(application: Application, message: str) -> None:
#     await application.bot.send_message(chat_id=185639289, text=message)


async def send_message(chat_id: Application, message: str) -> None:
    application = ApplicationBuilder().token(os.environ["TELEGRAM_API_TOKEN"]).build()
    await application.bot.send_message(chat_id=chat_id, text=message)


"""
>>> update.effective_chat
Chat(first_name='David', id=185639289, type=<ChatType.PRIVATE>, username='dtgoitia')
"""


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    config = get_config()

    application = ApplicationBuilder().token(os.environ["TELEGRAM_API_TOKEN"]).build()

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)

    application.run_polling()
