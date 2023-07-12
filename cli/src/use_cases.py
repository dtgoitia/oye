from src.config import Config
from src.devex import todo
from src.model import Reminder, ReminderId, Utterance
from src.oye import OyeClient


def add_reminder(utterance: Utterance, config: Config) -> Reminder:
    oye = OyeClient(config=config)
    added = oye.add_reminder(utterance=utterance)
    return added


def get_reminder(reminder_id: ReminderId, config: Config) -> Reminder | None:
    oye = OyeClient(config=config)
    reminder = oye.get_reminder(reminder_id=reminder_id)
    return reminder


def get_reminders(config: Config) -> list[Reminder]:
    oye = OyeClient(config=config)
    return oye.get_reminders()


def delete_reminder(reminder_id: ReminderId, config: Config) -> Reminder | None:
    oye = OyeClient(config=config)
    reminder = oye.delete_reminder(reminder_id=reminder_id)
    return reminder


def delete_reminder_interactive(config: Config) -> None:
    def _let_user_choose(reminders: list[Reminder]) -> list[ReminderId]:
        for n, reminder in enumerate(reminders, start=1):
            print(f"{str(n):<2}  {reminder.description}")

        print("Input the remiders you want to delete. Separate them by spaces if you want to delete many.")
        while True:
            answer = input("Reminders to delete: ").strip()
            try:
                indexes = list(map(int, answer.split(" ")))
            except Exception:
                print("Please input numbers separated by spaces")
                continue

            if min(indexes) <= 0 or max(indexes) > len(reminders):
                print(f"Numbers must be between 1 and {len(reminders)} (both included), try again")
                continue

            try:
                reminders_ids = [reminders[index - 1].id for index in indexes]
            except IndexError:
                print("Some number seems not to match the ones proposed above, try again")
                continue

            return reminders_ids

    oye = OyeClient(config=config)

    reminders = get_reminders(config=config)
    if not reminders:
        print("No reminders found")

    to_delete = _let_user_choose(reminders=reminders)

    for reminder_id in to_delete:
        reminder = oye.delete_reminder(reminder_id=reminder_id)
        if reminder is None:
            print(f"failed to delete reminder {reminder_id}")
