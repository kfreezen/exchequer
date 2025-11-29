from python_api.settings import Settings
from python_api.sso import BaseSSO

_client_ids = []


class GoogleSSO(BaseSSO):
    def __init__(self, settings: Settings, keys: list[dict[str, str]]):
        global _client_ids

        if not _client_ids:
            try:
                with open(settings.google_client_ids_file) as f:
                    _client_ids = f.readlines()
            except FileNotFoundError:
                _client_ids = []

        super().__init__(
            keys,
            [settings.google_client_id] + [i.strip() for i in _client_ids],
            ["https://accounts.google.com", "accounts.google.com"],
        )
