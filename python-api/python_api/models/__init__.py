from typing import Annotated
from uuid import UUID
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    PlainSerializer,
)
from humps import camelize

from datetime import datetime, UTC


def isoformat(d: datetime):
    d2 = d.astimezone(UTC) if not d.tzinfo else d
    return d2.isoformat(timespec="seconds")


DateTime = Annotated[datetime, PlainSerializer(isoformat, return_type=str)]


def _coerce_to_int(v):
    if v is None:
        return 0
    return int(v)


CoerceToInt = Annotated[int, BeforeValidator(_coerce_to_int)]


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=camelize, populate_by_name=True)


def _str(s):
    return str(s)


UUIDString = Annotated[
    UUID, AfterValidator(str), PlainSerializer(_str, return_type=str)
]
