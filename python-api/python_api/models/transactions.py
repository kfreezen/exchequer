from datetime import date as date_type, datetime
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


class TransactionUpdate(CamelModel):
    amount: Decimal | None = None
    date: date_type | None = None
    description: str | None = None
    envelope_id: str | None = None
    entity_id: str | None = None


class TransactionCreate(CamelModel):
    amount: Decimal
    date: date_type
    description: str | None = None
    envelope_id: str | None = None
    entity_id: str | None = None
