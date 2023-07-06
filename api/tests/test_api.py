import pytest
from sanic_testing.testing import SanicASGITestClient

from src.adapters.api import api


@pytest.mark.asyncio
async def test_add_reminder() -> None:
    client: SanicASGITestClient = api.asgi_client

    _, response = await client.get("/reminder")
    assert response.status == 200
    assert response.json
