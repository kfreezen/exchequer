from enum import Enum
from typing import Annotated
from uuid import UUID, uuid4
from pydantic import AfterValidator, BaseModel, Field, EmailStr, PlainSerializer
from datetime import datetime
from python_api.models import CamelModel, DateTime, isoformat, CoerceToInt


def _str(s):
    return str(s)


UUIDString = Annotated[
    UUID, AfterValidator(str), PlainSerializer(_str, return_type=str)
]


class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"


class TokenData(BaseModel):
    email: str | None = None


def _user_id():
    return uuid4()


class SsoUser(CamelModel):
    id: str
    provider: str
    user_id: UUIDString


class AppUserUpdate(CamelModel):
    name: str


class SsoConnectionType(str, Enum):
    GOOGLE = "google"
    FACEBOOK = "facebook"
    MICROSOFT = "microsoft"
    APPLE = "apple"
    GITHUB = "github"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    OTHER = "other"


class User(CamelModel):
    id: UUIDString = Field(default_factory=_user_id)
    email: EmailStr
    email_id: UUIDString | None = None

    name: str

    is_verified: bool = False
    restricted: bool = False

    roles: list[UserRole] = Field(default_factory=list)

    created_at: DateTime | None = None

    sso_connections: list[SsoConnectionType | None] = Field(default_factory=list)
    has_password: bool = False


class AdminUserViewModel(CamelModel):
    id: UUIDString
    name: str
    email: EmailStr

    restricted: bool = False

    is_verified: bool = False
    roles: list[UserRole] = Field(default_factory=list)

    sso_connections: list[SsoConnectionType] = Field(default_factory=list)


class AppUser(CamelModel):
    name: str
    email: EmailStr
    password: str
    subscription: str
    billing_period: str
    promo: bool = False


class UnverifiedUser(CamelModel):
    id: UUIDString = Field(default_factory=_user_id)
    name: str
    email: EmailStr
    is_verified: bool = False
    status: bool | None = None
    code: str | None = None
    code_expires_at: DateTime | None = None


class DbUser(User):
    password_hash: str

    linked_stripe_id: str | None = None
    requested_subscription: str | None = None
    requested_billing_period: str | None = None


class DbUserToken(BaseModel):
    id: str
    refresh_token: str
    date: int
    provider: str
    user_id: UUIDString
    sso_id: str | None = None
    last_used: int | None = None


class Token(CamelModel):
    token: str
    refresh_token: str
    user: User


class VerifyEmailCode(CamelModel):
    code: str


class UpdatePassword(CamelModel):
    old_password: str
    new_password: str
