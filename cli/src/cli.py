import logging

import click

from src import use_cases
from src.config import get_config
from src.devex import todo
from src.model import Once, Reminder

logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    logger.debug("cli invoked")


@cli.command(name="add")
@click.argument("utterance")
def add_reminder_cmd(utterance: str) -> None:
    logger.debug("add reminder")
    config = get_config()
    reminder = use_cases.add_reminder(utterance=utterance, config=config)
    print(reminder)


@cli.command(name="help")
def help_cmd() -> None:
    context = click.get_current_context()
    print(cli.get_help(context))


def _format_reminder(reminder: Reminder) -> str:
    schedule: str | None = None
    match reminder.schedule:
        case Once():
            schedule = f"{reminder.schedule.at.isoformat()}"
        case _:
            todo(f"must add support to new reminder: {reminder}")

    return f"{reminder.description}   {schedule}"


@cli.command(name="list")
def get_reminders_cmd() -> None:
    logger.debug("list reminders")
    config = get_config()
    reminders = use_cases.get_reminders(config=config)
    for reminder in reminders:
        print(_format_reminder(reminder))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    cli()
