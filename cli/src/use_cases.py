from src.config import Config
from src.devex import todo
from src.model import Reminder, Utterance
from src.oye import OyeClient


def add_reminder(utterance: Utterance, config: Config) -> Reminder:
    oye = OyeClient(config=config)
    added = oye.add_reminder(utterance=utterance)
    return added


def delete_reminder(config: Config) -> None:
    oye = OyeClient(config=config)
    reminders = oye.get_reminders()
    todo("allow user to choose which reminder to delete from list")
    reminder: Reminder = ...
    oye.delete(reminder_id=reminder.id)


def get_reminders(config: Config) -> list[Reminder]:
    oye = OyeClient(config=config)
    return oye.get_reminders()
