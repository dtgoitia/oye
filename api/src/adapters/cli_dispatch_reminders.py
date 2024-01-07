import asyncio
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder

from src.config import Config, get_config


async def amain(config: Config) -> None:
    application = ApplicationBuilder().token(os.environ["TELEGRAM_API_TOKEN"]).build()
    bot = application.bot

    async def send_message(chat_id: str, message: str, reply_markup) -> None:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=reply_markup,
        )

    # TODO:
    # get from DB all reminders whose `next_ocurrence` < now and dispatched = False
    # dispatch them to the telegram bot API so that Telegram pings user device
    reminders = [
        dict(
            chat_id="-1001998360297",
            message="hola!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    #    [  1  ][  2  ]
                    #    [      3     ]
                    [
                        # https://core.telegram.org/bots/api#inlinekeyboardbutton
                        InlineKeyboardButton(text="foo", url="https://example.com"),
                        InlineKeyboardButton(text="bar", url="https://example.com"),
                    ],
                    [
                        InlineKeyboardButton(text="baz", callback_data="button_3_pressed"),
                    ],
                ],
            ),
        ),
    ]

    tasks = [
        asyncio.create_task(
            send_message(
                chat_id=reminder["chat_id"],
                message=reminder["message"],
                reply_markup=reminder["reply_markup"],
            )
        )
        for reminder in reminders
    ]

    await asyncio.gather(*tasks)


def main() -> None:
    config = get_config()

    asyncio.run(amain(config=config))


if __name__ == "__main__":
    main()
