from datetime import datetime
from enum import Enum

from pydantic import Field
from python_api.models import CamelModel, UUIDString
from python_api.models.envelopes import Envelope


class EntityType(str, Enum):
    PERSONAL = "personal"
    BUSINESS = "business"


class Entity(CamelModel):
    id: UUIDString
    user_id: UUIDString

    type: EntityType
    name: str

    created_at: datetime
    updated_at: datetime

    envelopes: list[Envelope] = Field(default_factory=list)
