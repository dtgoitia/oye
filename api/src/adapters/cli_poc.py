import sys
from urllib.parse import urljoin

import requests  # type: ignore

from src.config import get_config


def main() -> None:
    config = get_config()

    response = requests.post(
        url=urljoin(config.api_base_url, "reminder"),
        json={
            "utterance": "at 10:30pm fooootterance for you!",
            "timezone": "+00:00",
        },
    )

    if not response.ok:
        print(response.text, file=sys.stderr)
    else:
        print(response)


if __name__ == "__main__":
    main()
