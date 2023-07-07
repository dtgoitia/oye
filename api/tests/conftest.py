from typing import AsyncIterator

import aiosqlite
import pytest
import pytest_asyncio
from aiosqlite import Connection

from src.adapters.clients.db import create_tables_if_needed
from src.config import Config
from tests import factories


@pytest.fixture
def config() -> Config:
    return factories.get_test_config()


@pytest_asyncio.fixture
async def db(config: Config) -> AsyncIterator[Connection]:
    async with aiosqlite.connect(database=config.db_uri) as db:
        await create_tables_if_needed(db=db)

        await db.execute("BEGIN;")

        yield db

        await db.rollback()
