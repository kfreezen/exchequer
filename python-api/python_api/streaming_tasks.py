import json
from faststream import FastStream
from faststream.redis import RedisBroker, StreamSub
from python_api.models.actions import UserAction, UserSubscriptionAction
from python_api.repositories.transactions import TransactionsRepository

from python_api.settings import Settings
from python_api.task_deps import async_conn

settings = Settings()

broker = RedisBroker(settings.redis_url)
app = FastStream(broker=broker)


@broker.subscriber(stream=StreamSub("transactions", batch=True, polling_interval=1000))
async def transactions_handler(messages: list[dict[str, str]]):
    transactions = [json.loads(message["data"]) for message in messages]
    async with async_conn() as conn:
        repo = TransactionsRepository(conn)
        for transaction in transactions:
            await repo.insert_transaction(**transaction)


@broker.subscriber(stream=StreamSub("user-actions", batch=True, polling_interval=1000))
async def user_actions_handler(messages: list[dict[str, str]]):
    actions = [UserAction.model_validate_json(message["data"]) for message in messages]
    async with async_conn() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(
                """
                INSERT INTO user_actions (action, user_id, info, occurred_at, stream_id)
                VALUES (
                    %(action)s,
                    %(user_id)s,
                    %(info)s,
                    %(occurred_at)s,
                    %(stream_id)s
                )
                """,
                [action.model_dump(mode="json", by_alias=False) for action in actions],
            )
            await conn.commit()


@broker.subscriber(
    stream=StreamSub("user-subscription-actions", batch=True, polling_interval=500)
)
async def user_subscription_actions_handler(messages: list[dict[str, str]]):
    actions = [
        UserSubscriptionAction.model_validate_json(message["data"])
        for message in messages
    ]
    async with async_conn() as conn:
        async with conn.cursor() as cur:
            action_dumps = [
                action.model_dump(mode="json", by_alias=False) for action in actions
            ]

            for dump in action_dumps:
                dump["info"] = json.dumps(dump["info"])

            await cur.executemany(
                """
                INSERT INTO user_subscription_actions (action, user_id, info, occurred_at, stream_id)
                VALUES (
                    %(action)s,
                    %(user_id)s,
                    %(info)s,
                    %(occurred_at)s,
                    %(stream_id)s
                )
                """,
                action_dumps,
            )
            await conn.commit()
