from python_api.models import CamelModel


class BaseAction(CamelModel):
    """Base class for all actions."""

    id: int | None = None

    action: str
    info: dict | None = None

    occurred_at: int
    stream_id: str | None = None


class UserAction(BaseAction):
    user_id: str | None = None


class UserSubscriptionAction(UserAction):
    pass


class SystemAction(BaseAction):
    user_action_id: int | None = None
