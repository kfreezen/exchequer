from datetime import datetime
from enum import Enum

from pydantic import Field
from python_api.models import CamelModel, UUIDString
from python_api.models.transactions import Transaction


class EnvelopeType(str, Enum):
    MASTER_INCOME = "master-income"
    MASTER_EXPENSE = "master-expense"

    ACCOUNT = "account"
    ENVELOPE = "envelope"


class EnvelopeCreate(CamelModel):
    name: str
    type: EnvelopeType


class Envelope(CamelModel):
    id: UUIDString
    entity_id: UUIDString | None = None

    name: str

    created_at: datetime
    updated_at: datetime


class EnvelopeWithTransactionCounts(Envelope):
    unassigned_transaction_count: int | None = Field(
        None, description="Number of unassigned transactions for this envelope"
    )


class EnvelopeWithTransactions(Envelope):
    transactions: list[Transaction] = Field(
        default_factory=list,
        description="List of transactions associated with this envelope",
    )
