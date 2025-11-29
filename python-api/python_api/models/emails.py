from typing import Any
from . import CamelModel
from pydantic import BaseModel
from enum import Enum
from python_api.models.users import UUIDString


class EmailType(Enum):
    PROMOTIONAL = "promotional"
    TRANSACTIONAL = "transactional"


class AutomatedEmail(BaseModel):
    id: int | None = None
    user_id: UUIDString
    user_email: str | None = None
    email_type: EmailType
    subject: str
    template: str
    variables: dict[str, Any] | None = None
    scheduled_at: int
    sent_at: int | None = None
