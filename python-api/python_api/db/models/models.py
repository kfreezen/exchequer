from datetime import datetime, date as dt_date, timedelta
import enum
from decimal import Decimal
from typing import Any
from sqlalchemy.dialects.postgresql import (
    BOOLEAN,
    INTEGER,
    FLOAT,
    INTERVAL,
    JSON,
    JSONB,
    TEXT,
    UUID,
    VARCHAR,
)
from sqlalchemy.orm import Mapped

from python_api.db.models.base import TZ_TIMESTAMP
from .base import (
    Bool,
    Int,
    Float,
    NullableInt,
    Str,
    NullableStr,
    default_null,
    Base,
    primary_key,
    mapped_column,
    text_column,
    generic_fkey,
    user_id_fkey,
)
from sqlalchemy import (
    Enum,
    BIGINT,
    NUMERIC,
    ForeignKey,
    Integer,
    Sequence,
    sql,
    UniqueConstraint,
    text,
    ARRAY,
)


class TokenProvider(enum.Enum):
    EXCHEQUER = "EXCHEQUER"
    APPLE = "APPLE"
    GOOGLE = "GOOGLE"


TOKEN_PROVIDER = Enum(TokenProvider, name="token_providers")


class PasswordReset(Base):
    __tablename__ = "password_reset"
    id: Str = mapped_column(UUID, primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(TZ_TIMESTAMP)
    code: Str = text_column()
    user_id: Str = mapped_column(
        UUID,
        ForeignKey("users.id", name="password_reset_user_id_fkey", ondelete="CASCADE"),
        nullable=True,  # TODO: Set non-null?
    )


VERIFICATION_SEQ = Sequence("verification_id_seq")


class Verification(Base):
    __tablename__ = "verification"
    id: Mapped[int] = mapped_column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        server_default=VERIFICATION_SEQ.next_value(),
    )
    code: Str = text_column(nullable=True)
    expires_at: Mapped[datetime] = mapped_column(TZ_TIMESTAMP, nullable=True)
    user_id: Str = mapped_column(
        UUID,
        ForeignKey("users.id", name="verification_user_id_fkey", ondelete="CASCADE"),
    )
    status: Mapped[bool]


class SSOUser(Base):
    __tablename__ = "sso_users"

    id: Str = mapped_column(VARCHAR(128), primary_key=True)
    provider: Str = text_column(nullable=True)
    user_id: Str = mapped_column(
        UUID,
        ForeignKey("users.id", name="sso_users_user_fkey", ondelete="CASCADE"),
        nullable=False,
    )  # TODO: This should probably be nullable=False


class User(Base):
    __tablename__ = "users"

    id: Str = mapped_column(UUID, primary_key=True)

    name: Str = mapped_column(TEXT)
    email: Str = mapped_column(TEXT, unique=True)
    email_id: Str = mapped_column(
        UUID, unique=True, server_default=text("uuid_generate_v4()")
    )
    password_hash: Mapped[bytes] = mapped_column(TEXT)
    roles: Mapped[list[str]] = mapped_column(ARRAY(TEXT))
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=True)
    restricted: Mapped[bool] = mapped_column(default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(TZ_TIMESTAMP, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(TZ_TIMESTAMP, nullable=True)
    deleted_at: Mapped[datetime] = mapped_column(TZ_TIMESTAMP, nullable=True)


class UserSubscriptionAction(Base):
    __tablename__ = "user_subscription_actions"

    id: Int = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    user_id: Str = user_id_fkey("user_subscription_actions_user_id_fkey")

    action: Str = text_column(nullable=False)
    info: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True)

    occurred_at: Int = mapped_column(BIGINT, nullable=False)
    stream_id: Str = mapped_column(TEXT, nullable=True, unique=True)


class UserAction(Base):
    __tablename__ = "user_actions"

    id: Int = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    user_id: Str = user_id_fkey("user_actions_user_id_fkey", nullable=True)

    action: Str = text_column(nullable=False)
    info: Mapped[dict] = mapped_column(JSONB, nullable=True)

    occurred_at: Int = mapped_column(BIGINT, nullable=False)
    stream_id: Str = mapped_column(TEXT, nullable=True, unique=True)


class SystemAction(Base):
    __tablename__ = "system_actions"

    id: Int = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    action: Str = text_column(nullable=False)
    info: Mapped[dict] = mapped_column(JSONB, nullable=True)

    occurred_at: Int = mapped_column(BIGINT, nullable=False)
    stream_id: Str = mapped_column(TEXT, nullable=True, unique=True)

    user_action_id: Int = generic_fkey(
        BIGINT,
        "user_actions.id",
        "system_actions_user_action_id_fkey",
        nullable=True,
        ondelete="SET NULL",
    )


class UserToken(Base):
    __tablename__ = "user_tokens"

    id: Str = text_column(primary_key=True)
    refresh_token: Str = text_column()
    provider: Mapped[TokenProvider] = mapped_column(TOKEN_PROVIDER)
    user_id = user_id_fkey(
        "user_tokens_user_id_fkey", ondelete="CASCADE", nullable=False
    )
    date: Mapped[int] = mapped_column(
        BIGINT, default=0
    )  # FIXME: Change default for this.
    last_used: Mapped[int] = mapped_column(BIGINT, nullable=True)

    sso_id: Str = mapped_column(
        VARCHAR(128),
        ForeignKey("sso_users.id", name="user_tokens_sso_fkey"),
        nullable=True,
    )


class ErrorLog(Base):
    __tablename__ = "error_log"

    id: Int = primary_key(autoincrement=True)

    user_id: Str = mapped_column(
        UUID,
        ForeignKey("users.id", name="user_error_log_user_fkey", ondelete="SET NULL"),
        nullable=True,
    )

    severity: Int = mapped_column(Integer, nullable=False)
    type: Str = mapped_column(TEXT, nullable=False)

    created_at: Mapped[datetime] = mapped_column(TZ_TIMESTAMP, nullable=False)
    endpoint: Str = mapped_column(TEXT, nullable=True)
    status_code: Int = mapped_column(BIGINT, nullable=True)

    details: Mapped[dict] = mapped_column(JSONB, nullable=True)


class AutomatedEmail(Base):
    __tablename__ = "automated_emails"

    id: Int = primary_key(autoincrement=True)

    user_id: Str = mapped_column(
        UUID,
        ForeignKey("users.id", name="automated_email_user_fkey", ondelete="SET NULL"),
        nullable=True,
    )

    email_type: Str = mapped_column(TEXT)
    template: Str = mapped_column(TEXT)

    subject: Str = mapped_column(TEXT)
    variables: Mapped[dict] = mapped_column(JSONB, nullable=True)

    scheduled_at: Int = mapped_column(BIGINT)
    sent_at: Int = mapped_column(BIGINT, nullable=True)


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Int = primary_key(autoincrement=True)

    user_id: Str = mapped_column(
        UUID,
        ForeignKey("users.id", name="user_subscription_user_fkey", ondelete="SET NULL"),
        nullable=True,
    )

    subscribed_at = mapped_column(BIGINT, nullable=False)
    unsubscribed_at = mapped_column(BIGINT, nullable=True)

    email_type: Str = mapped_column(TEXT, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Str = mapped_column(UUID, primary_key=True)
    user_id: Str = mapped_column(
        UUID,
        ForeignKey("users.id", name="transaction_user_id_fkey", ondelete="SET NULL"),
        nullable=True,
    )

    source: Str = text_column()
    transaction_id: Str = text_column(nullable=True)
    product_id: Str = text_column(nullable=True)
    price: Mapped[Decimal] = mapped_column(NUMERIC, nullable=True)
    tax_percentage: Mapped[Decimal] = mapped_column(NUMERIC, nullable=True)
    commission_percentage: Mapped[Decimal] = mapped_column(NUMERIC, nullable=True)
    takehome_percentage: Mapped[Decimal] = mapped_column(NUMERIC, nullable=True)
    takehome_amount: Mapped[Decimal] = mapped_column(NUMERIC, nullable=False)

    created_at: Int = mapped_column(BIGINT, nullable=False, index=True)
    transacted_at: Int = mapped_column(BIGINT, nullable=True, index=True)

    # applied_at helps us track when to apply a transaction to a user's account.
    # this way, we can create amortization transactions right away.
    applied_at: Int = mapped_column(BIGINT, nullable=True, index=True)

    amortized_transaction_id: Str = mapped_column(UUID, nullable=True)
    currency: Str = text_column(nullable=True)

    __table_args__ = (
        UniqueConstraint("transaction_id", "source", name="uq_transaction_id_source"),
    )
