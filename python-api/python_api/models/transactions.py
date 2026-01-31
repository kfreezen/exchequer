from datetime import datetime
from decimal import Decimal
from python_api.models import CamelModel, UUIDString


class Transaction(CamelModel):
    id: UUIDString
    amount: Decimal
    date: datetime
    entity_id: UUIDString | None = None
    payee_id: UUIDString | None = None
    payee_name: str | None = None

    description: str | None = None
    envelope_id: UUIDString | None = None
    created_at: datetime
    updated_at: datetime
