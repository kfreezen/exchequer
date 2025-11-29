from sqlalchemy import (
    TEXT,
    UUID,
    ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column as mapped_column
from sqlalchemy.dialects.postgresql import TIMESTAMP

NullableStr = Mapped[str | None]
Str = Mapped[str]
Int = Mapped[int]
Float = Mapped[float]
NullableInt = Mapped[int | None]
Bool = Mapped[bool]
TZ_TIMESTAMP = TIMESTAMP(timezone=True)


def default_null(*args):
    return mapped_column(*args, default=None)


def primary_key(*args, **kwargs):
    return mapped_column(*args, primary_key=True, **kwargs)


def text_column(*args, **kwargs):
    return mapped_column(TEXT, *args, **kwargs)


def generic_fkey(_type, fkey, name, ondelete: str | None = None, **kwargs):
    return mapped_column(
        _type, ForeignKey(fkey, name=name, ondelete=ondelete), **kwargs
    )


def user_id_fkey(name, ondelete: str | None = None, **kwargs):
    return generic_fkey(UUID, "users.id", name, ondelete=ondelete, **kwargs)


class Base(DeclarativeBase):
    pass
