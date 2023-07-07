import datetime
from dataclasses import replace

from src.config import Config
from src.domain.reminders import Once
from src.main import Engine, Reminder, ReminderRepository, UniqueHeapQueue
from tests.factories import d


def test_once_next_occurrence() -> None:
    t = datetime.datetime.now()
    schedule = Once(at=t)
    assert schedule.next_occurrence == t


def test_tick():
    queue = UniqueHeapQueue()
    t1 = d("2023-07-05 00:00:01 +01:00")
    t2 = d("2023-07-05 00:00:02 +01:00")
    t3 = d("2023-07-05 00:00:03 +01:00")
    t4 = d("2023-07-05 00:00:04 +01:00")

    queue.add([t3, t1, t4, t2])

    # until a limit inside the dates in the queue
    assert list(queue.pop_occurrences(until=d("2023-07-05 00:00:04 +01:00"))) == [
        t1,
        t2,
        t3,
    ]

    # until a limit beyond the values in the queue
    assert list(queue.pop_occurrences(until=d("2023-07-05 00:00:09 +01:00"))) == [
        t4,
    ]


def test_queue_peek_all_returns_sorted_occurrences():
    queue = UniqueHeapQueue()
    t1 = d("2023-07-05 00:00:01 +01:00")
    t2 = d("2023-07-05 00:00:02 +01:00")
    t3 = d("2023-07-05 00:00:03 +01:00")
    t4 = d("2023-07-05 00:00:04 +01:00")

    queue.add([t3, t1, t4, t2])
    assert list(queue.peek_all()) == [t1, t2, t3, t4]


def test_queue_ignores_duplicates():
    queue = UniqueHeapQueue()
    t1 = d("2023-07-05 00:00:01 +01:00")
    t2 = d("2023-07-05 00:00:02 +01:00")

    queue.add([t1, t2])
    assert set(queue.peek_all()) == {t1, t2}

    queue.add([t1])
    assert set(queue.peek_all()) == {t1, t2}


def test_reminder_manager():
    man = ReminderRepository()

    man.add(
        Reminder(
            id="rem_00000000",
            description="do foo",
            schedule=Once(at=d("2023-07-05 00:00:01 +01:00")),
        ),
    )
    man.add(
        Reminder(
            id="rem_11111111",
            description="do bar",
            schedule=Once(at=d("2023-07-05 00:00:01 +01:00")),
        ),
    )
    man.add(
        Reminder(
            id="rem_22222222",
            description="do baz",
            schedule=Once(at=d("2023-07-05 00:00:09 +01:00")),
        ),
    )
    man.add(
        Reminder(
            id="rem_33333333",
            description="do bazzzz",
            schedule=Once(at=d("2023-07-05 00:00:10 +01:00")),
        ),
    )

    reminders = man.get_reminders_from(
        occurrences=iter(
            [
                d("2023-07-05 00:00:01 +01:00"),
                d("2023-07-05 00:00:09 +01:00"),
            ]
        )
    )
    assert {r.id for r in reminders} == {
        "rem_00000000",
        "rem_11111111",
        "rem_22222222",
        # "rem_33333333"  <--- not this one
    }


def test_engine_notifies_reminders_with_occurences_prior_to_the_tick(config: Config) -> None:
    config = replace(config, engine_tick_delta=10)

    # Given:
    notified: list[Reminder] = []

    def _mock_notifier(reminder: Reminder) -> None:
        nonlocal notified
        notified.append(reminder)

    reminder_a = Reminder(
        id="rem_00000000",
        description="do foo",
        schedule=Once(at=d("2023-07-05 00:00:01 +01:00")),
    )
    reminder_b = Reminder(
        id="rem_11111111",
        description="do bar",
        schedule=Once(at=d("2023-07-05 00:00:13 +01:00")),
    )
    reminder_c = Reminder(
        id="rem_22222222",
        description="do baz",
        schedule=Once(at=d("2023-07-06 00:00:00 +01:00")),
    )

    engine = Engine(
        manager=ReminderRepository(),
        notify_cb=_mock_notifier,
        config=config,
    )

    engine._last_tick = d("2023-07-05 00:00:02 +01:00")

    engine.create_reminder(reminder_a)
    engine.create_reminder(reminder_b)
    engine.create_reminder(reminder_c)

    # when the engine ticks
    engine.tick()

    # then engine notifies only the reminders prior to the next tick
    # (where next_tick = last_tick + tick_delta)
    assert notified == [reminder_a]

    # given the notified mock is cleaned
    notified = []

    # when the engine ticks
    engine.tick()

    # then engine notifies only the reminders prior to the next tick
    # (where next_tick = last_tick + tick_delta)
    assert notified == [reminder_b]