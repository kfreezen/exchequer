from datetime import datetime

from python_api.models import CamelModel, UUIDString


class Plan(CamelModel):
    id: UUIDString
    name: str
    currency_code: str | None = None

    created_at: datetime
    updated_at: datetime

    import_id: UUIDString | None = None
