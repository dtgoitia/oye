import aiohttp
from apischema import deserialize

from src.adapters.api.crud import ApiRoutes
from src.config import Config
from src.main import Reminder
from src.model import JsonDict, Utterance


class ContextManagerNeeded(Exception):
    ...


class OyeClient:
    def __init__(self, config: Config) -> None:
        self._config = config

    async def __aenter__(self):
        self._client = aiohttp.ClientSession(
            base_url=self._config.api_base_url,
            # auth=
        )
        return self

    async def __aexit__(self, *err):
        if not self._client:
            return

        await self._client.close()

    async def _get(self, *, url: str) -> JsonDict:
        if self._client is None:
            raise ContextManagerNeeded()

        async with self._client.get(url=url) as response:
            response.raise_for_status()
            data: JsonDict = await response.json()
            return data

    async def _post(self, *, url: str, data: JsonDict) -> JsonDict:
        if self._client is None:
            raise ContextManagerNeeded()

        async with self._client.post(url=url, json=data) as response:
            response.raise_for_status()
            response_data: JsonDict = await response.json()
            return response_data

    async def get_reminders(self) -> list[Reminder]:
        payload = await self._get(url=ApiRoutes.reminders)
        reminders = payload["reminders"]
        return deserialize(list[Reminder], reminders)

    async def add_reminder(self, utterance: Utterance) -> None:
        await self._post(url=ApiRoutes.reminders, data={"utterance": utterance})
