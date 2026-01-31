from python_api.models import CamelModel, UUIDString
from datetime import datetime


class Account(CamelModel):
    id: UUIDString
    user_id: UUIDString
    name: str
    type: str
    closed: bool
    created_at: datetime
    updated_at: datetime
    import_id: UUIDString | None = None
