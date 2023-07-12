from typing import Literal, TypeAlias

import requests
from apischema import deserialize

from src.config import Config
from src.model import JsonDict, Reminder, ReminderId, Utterance

HttpMethod: TypeAlias = Literal["GET", "POST", "DELETE"]


class OyeClient:
    def __init__(self, config: Config) -> None:
        self._base_url = config.oye_api_url
        self._session = requests.Session()

    def _request(self, method: HttpMethod, url: str, data: JsonDict | None = None) -> JsonDict:
        _url = f"{self._base_url}/{url}"
        response = self._session.request(
            method=method,
            url=_url,
            json=data,
        )

        response.raise_for_status()

        return response.json()

    def _get(self, *, url: str) -> JsonDict:
        return self._request(method="GET", url=url)

    def _post(self, *, url: str, data: JsonDict) -> JsonDict:
        return self._request(method="POST", url=url, data=data)

    def _delete(self, *, url: str) -> JsonDict:
        return self._request(method="DELETE", url=url)

    def add_reminder(self, utterance: Utterance) -> Reminder:
        response = self._post(url="reminder", data={"utterance": utterance})
        return deserialize(Reminder, response["added_reminder"])

    def get_reminder(self, reminder_id: ReminderId) -> Reminder | None:
        try:
            response = self._get(url=f"reminder/{reminder_id}")
        except requests.exceptions.HTTPError as e:
            if e.response is not None and (e.response.status_code == 404):
                return None
            else:
                raise

        return deserialize(Reminder, response["reminder"])

    def delete_reminder(self, reminder_id: ReminderId) -> Reminder | None:
        response = self._delete(url=f"reminder/{reminder_id}")
        return deserialize(Reminder, response["deleted_reminder"])

    def get_reminders(self) -> list[Reminder]:
        response = self._get(url="reminder")
        return deserialize(list[Reminder], response["reminders"])
