from datetime import datetime
from enum import Enum

from pydantic import Field
from python_api.models import CamelModel, UUIDString


class EnvelopeType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Envelope(CamelModel):
    id: UUIDString
    user_id: UUIDString
    entity_id: UUIDString

    name: str
    type: EnvelopeType

    created_at: datetime
    updated_at: datetime
