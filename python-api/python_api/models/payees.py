from python_api.models import CamelModel, UUIDString
from datetime import datetime


class Payee(CamelModel):
    id: UUIDString
    name: str

    created_at: datetime
    updated_at: datetime

    import_id: UUIDString | None = None
