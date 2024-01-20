```shell
# start a service to CRUD reminders via HTTP (used by CLI)
make run_api

# start a service to communicate with the Telegram Bot API
make run_telegram_bot

# dispatches reminders every some seconds
make run_reminder_dispatcher

# recalculates `next_occurrences` every some seconds
make run_next_occurrence_calculator

# CLI to add reminders
python -m src.adapters.cli.add_reminder
```

next: see wipman
