from redis.asyncio import Redis
from datetime import datetime

import json

from python_api.models.actions import UserSubscriptionAction


class Tracking:
    def __init__(self, redis: Redis, user_id: str | None):
        self.redis = redis
        self.user_id = user_id

    async def track_subscription_action(self, action, info):
        if hasattr(info, "model_dump"):
            info = info.model_dump(by_alias=True, mode="json")

        action = UserSubscriptionAction(
            user_id=self.user_id,
            action=action,
            info=info,
            occurred_at=int(datetime.now().timestamp()),
        )

        await self.redis.xadd(
            "user-subscription-actions",
            {"data": action.model_dump_json(by_alias=True)},
        )
        pass

    async def track_transaction(self, transaction):
        await self.redis.xadd("transactions", {"data": json.dumps(transaction)})
