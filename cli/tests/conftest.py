import pytest

from src.config import Config
from tests import factories


@pytest.fixture
def config() -> Config:
    return factories.get_test_config()
