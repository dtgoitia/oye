# Architectural design

DB = source of truth

user --> CLI --> reminder API (long running) --> DB

every 1 min --> read DB and fire reminders


## CRUD user journey is clear

user --> CLI ----------------------------------> reminder API (long running) --> DB
user --> Telegram --> bot API (long running) --> reminder API (long running) --> DB

## Reminder trigger

previous implementation:
  - asyncio long running process
  - reads reminder definitions from DB
  - calculates next-reminder from reminder definitions and stores it in memory
  - every 1 minute, an event is triggered to check in-memory next-reminders

POC phase: process is triggered by a Kubernetes CronJob that runs every 1 min
  - much simpler approach
  - external trigger (even a `watch -n 1`, but better a k8s CronJob) triggers a command
  - the command reads the DB, find those ready to fire (aka, `where next_occurrence < now`)
  - have another recurring job to calculate `next_occurrence` and write to DB
  - pro: much simpler to implement - you don't have thousands of users yet... you can redesign it later if you have performance issues
  - pro: having separate services helps to rewrite in different languages
