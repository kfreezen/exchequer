from contextlib import asynccontextmanager

from psycopg.rows import dict_row
from python_api.db_conn import AsyncConnection

from redis.asyncio import Redis

from python_api.settings import Settings
from python_api.repositories.automated_emails import AutomatedEmails

from python_api.services.bucket import FileBucket

from python_api.mail import Mailer, EmailGenerator

settings = Settings()


@asynccontextmanager
async def async_conn():
    async with await AsyncConnection.connect(
        settings.database_dsn, row_factory=dict_row
    ) as aconn:
        yield aconn


async def redis_dep():
    redis = Redis.from_url(settings.redis_url)
    return redis


async def automated_emails_dep(conn):
    return AutomatedEmails(settings, conn)


async def mailer_dep():
    # Note: if your settings are not working on dev environment
    # add smtp settings to .env in root directory
    return Mailer(settings)


async def email_generator_dep():
    return EmailGenerator(settings)


async def bucket_store_dep():
    return FileBucket(
        settings.bucket_storage
    )  # Note: Change to "/data/" for local development
