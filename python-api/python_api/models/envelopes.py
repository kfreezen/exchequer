from datetime import datetime
from enum import Enum

from pydantic import Field
from python_api.models import CamelModel, UUIDString


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
    user_id: UUIDString
    entity_id: UUIDString

    name: str
    type: EnvelopeType

    created_at: datetime
    updated_at: datetime
