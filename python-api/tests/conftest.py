from datetime import UTC, datetime, timedelta
from fastapi import Header
from fpdf import FPDF

from psycopg.rows import dict_row
import pytest
import psycopg
import logging
import json

from fastapi.testclient import TestClient

from alembic.config import Config
from alembic import command

from python_api.main import app
from python_api.dependencies import (
    PublisherRepositoryDep,
    TransactionsRepositoryDep,
    UserRepositoryDep,
    admin,
    bucket_storage,
    get_current_user,
    mailer,
    requires_valid_subscription,
    settings,
    valid_jwt,
)
from python_api.app_routers.users import revenue_cat
from python_api.revenuecat import RevenueCat
from python_api.settings import Settings
from python_api.models.users import DbUser, UserRole, User
from python_api.repositories.users import UserRepository


def is_redis_responsive(url):
    from redis import Redis

    try:
        conn = Redis.from_url(url)
        conn.ping()
        conn.close()
        return True
    except Exception as e:
        print("Redis not responsive at", url, e)
        return False


def is_postgres_responsive(url):
    try:
        conn = psycopg.connect(url)
        conn.close()
        return True
    except Exception:
        return False


class MailerMock:
    def __init__(self):
        self.calls = []

    def sendmail(self, to, subject, text, html=None):
        self.calls.append((to, subject, text, html))


class RCResponse:
    def __init__(self, json):
        self._json = json

    @property
    def is_error(self):
        return False

    def json(self):
        return self._json


@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def postgres_conn(postgres):
    async with await psycopg.AsyncConnection.connect(
        postgres, row_factory=dict_row
    ) as conn:
        yield conn


@pytest.fixture(scope="session")
async def redis_conn(redis):
    from redis.asyncio import Redis

    redis = Redis.from_url(redis)
    yield redis
    await redis.aclose()


@pytest.fixture(scope="session")
async def user_repo(postgres_conn):
    yield UserRepository(None, None, postgres_conn, Settings())


@pytest.fixture
async def test_user(user_repo: UserRepository):
    res = await user_repo.get_user_by_email("test@exchequer.local")
    assert res is not None

    return res


class BucketStorageMock:
    async def delete_bucket_file(self, _key, bucket):
        pass

    async def get_bucket_file(self, _key, bucket):
        return "__FAKE__.pdf"


@pytest.fixture
async def fake_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.output("__FAKE__.pdf")
    yield
    import os

    os.unlink("__FAKE__.pdf")


@pytest.fixture
def test_app(postgres, redis, test_user, user_repo):
    def override_settings():
        return Settings(
            database_dsn=postgres, redis_url=redis, revenuecat_webhook_secret="test"
        )

    async def override_get_current_user(x_current_user: str | None = Header(None)):
        if x_current_user is None:
            return test_user
        else:
            res = await user_repo.get_user_by_email(x_current_user)
            assert res is not None

            return res

        return test_user

    async def override_revenuecat(
        users: UserRepositoryDep, transactions: TransactionsRepositoryDep
    ):
        return RevenueCatMock(users, transactions)

    def override_mailer():
        return MailerMock()

    def override_bucket_storage():
        return BucketStorageMock()

    async def override_valid_jwt(
        x_current_user: str | None = Header(None),
    ):
        if x_current_user is None:
            return {
                "sub": test_user.id,
                "entitlements": {
                    "basic": (datetime.now(UTC) + timedelta(days=1)).isoformat()
                },
            }
        else:
            res = await user_repo.get_user_by_email(x_current_user)
            assert res is not None

            return {
                "sub": res.id,
                "entitlements": {
                    "basic": (datetime.now(UTC) + timedelta(days=1)).isoformat()
                },
            }

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[requires_valid_subscription] = lambda: None
    app.dependency_overrides[valid_jwt] = override_valid_jwt
    app.dependency_overrides[admin] = lambda: True
    app.dependency_overrides[settings] = override_settings
    app.dependency_overrides[revenue_cat] = override_revenuecat
    app.dependency_overrides[mailer] = override_mailer
    app.dependency_overrides[bucket_storage] = override_bucket_storage
    return app


@pytest.fixture
def test_client(test_app):
    with TestClient(test_app) as client:
        yield client


@pytest.fixture(scope="session")
def redis(docker_ip, docker_services):
    port = docker_services.port_for("test-redis", 6379)
    dsn = f"redis://{docker_ip}:{port}/0"
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_redis_responsive(dsn)
    )

    return dsn


@pytest.fixture(scope="session")
def postgres(docker_ip, docker_services):
    port = docker_services.port_for("test-postgres", 5432)
    dsn = f"postgresql://postgres:password@{docker_ip}:{port}/exchequer"
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_postgres_responsive(dsn)
    )

    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "alembic")
    alembic_cfg.set_main_option(
        "sqlalchemy.testurl", dsn.replace("postgresql:", "postgresql+psycopg:")
    )

    command.upgrade(alembic_cfg, "head")

    return dsn


@pytest.fixture(scope="session")
async def test_data(
    postgres,
    postgres_conn,
    user_repo,
    publisher_repo,
):
    import email_validator

    email_validator.SPECIAL_USE_DOMAIN_NAMES.remove("local")
    conn = postgres_conn
    user = DbUser(
        email="test@exchequer.local",
        name="Test User",
        roles=[UserRole.ADMIN],
        passwordHash=user_repo.get_password_hash("oldpassword"),
    )
    await user_repo.insert_user(user)
    user2 = DbUser(
        email="test2@exchequer.local",
        name="Test2 User",
        roles=[UserRole.ADMIN],
        passwordHash=user_repo.get_password_hash("oldpassword"),
    )
    await user_repo.insert_user(user2)
    await conn.commit()

    await conn.commit()

    yield postgres
