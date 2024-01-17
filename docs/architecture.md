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

- much simpler approach: small **separate services**, instead of everything in-memory in a single process

  - pro: much simpler to implement - you don't have thousands of users yet... you can redesign it later if you have performance issues
  - pro: having separate services helps to rewrite in different languages

- DB as a source of truth

  - phase 1: use sqlite
  - phase 2: support concurrent writes (postgresql)

- web API to CRUD reminders:

  - clients (CLI, Telegram, etc.) interact with this web API to CRUD reminders
  - stateless: source of truth = DB

- long-running process with Telegram bot:

  - purpose: allow user to CRUD reminders via Telegram
  - implementation: it's a proxy/adaptor that calls the web API to CRUD reminders

- send reminders:

  - external trigger (even a `watch -n 1`, but better a k8s CronJob) triggers a command
  - the command reads the DB, find those ready to fire (aka, `where next_occurrence < now`)
  - can scale, e.g.: spin up multiple instances of this worker, partitioned by user, and process in parallel
  - testable: easy to test in isolation, as the DB and Telegram API (mockable) is the only interface

- calculate next occurrences:
  - another CronJob to calculate `next_occurrence` and write it to DB
  - can scale, e.g.: spin up multiple instances of this worker, partitioned by user, and process in parallel
  - testable: easy to test in isolation, as the DB is the only interface

## `next_occurrence` calculator

- requirements:
  - the `reminders` table should only contain active reminders, do not keep completed reminders around. If you want to keep record of triggered reminders, build a separate table (where you can also track snoozes, etc.)

![][1]

<!-- External references -->

[1]: ./2024-01-07-141606-oye-architecture-overview.png
