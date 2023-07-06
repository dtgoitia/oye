from unittest.mock import ANY

import pytest
from sanic_testing.testing import SanicASGITestClient

from src.adapters.api import api


@pytest.mark.asyncio
async def test_add_reminder() -> None:
    client: SanicASGITestClient = api.asgi_client

    _, response = await client.get("/reminder")
    assert response.status == 200
    assert response.json == {
        "reminders": [
            {
                "id": ANY,
                "description": "do foo",
                "schedule": {"at": "2023-07-05T00:00:01+01:00"},
            },
            {
                "id": ANY,
                "description": "do bar",
                "schedule": {"at": "2023-07-05T00:00:13+01:00"},
            },
            {
                "id": ANY,
                "description": "do baz",
                "schedule": {"at": "2023-07-06T00:00:00+01:00"},
            },
        ]
    }

    utterance = "say foo in 5 mins"

    _, response = await client.post("/reminder", json={"utterance": utterance})
    assert response.status == 200
    assert response.json == {
        "added_reminder": {
            "id": ANY,
            "description": "say foo",
            "schedule": {"at": ANY},
        }
    }

    _, response = await client.get("/reminder")
    assert response.status == 200
    assert response.json == {
        "reminders": [
            {
                "id": ANY,
                "description": "do foo",
                "schedule": {"at": "2023-07-05T00:00:01+01:00"},
            },
            {
                "id": ANY,
                "description": "do bar",
                "schedule": {"at": "2023-07-05T00:00:13+01:00"},
            },
            {
                "id": ANY,
                "description": "do baz",
                "schedule": {"at": "2023-07-06T00:00:00+01:00"},
            },
            {
                "id": ANY,
                "description": "say foo",
                "schedule": {"at": ANY},
            },
        ]
    }
