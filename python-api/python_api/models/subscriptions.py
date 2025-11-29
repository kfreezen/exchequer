from datetime import datetime
from enum import Enum

from python_api.models import CamelModel
from python_api.models import UUIDString


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    TRIALING = "trialing"


class Subscription(CamelModel):
    id: UUIDString
    user_id: UUIDString

    stripe_subscription_id: str | None = None

    status: SubscriptionStatus

    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None
