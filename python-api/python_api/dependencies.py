from datetime import datetime, timedelta, timezone
import json
import asyncio
import traceback
from typing import Annotated, Any
from redis.asyncio import Redis
from jwcrypto.common import JWException

import os
import stripe

from fastapi import Header, Query, Request, status, Response
from python_api.sso import InvalidIDToken

from python_api.sso.google import GoogleSSO
from python_api.user_errors import UserErrors

from fastapi import Depends

from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer
import httpx
from psycopg.rows import DictRow, dict_row
from psycopg import AsyncConnection
from jwcrypto import jwk, jwt
from jwcrypto.jws import InvalidJWSSignature

from python_api.db_conn import LazyConnectionContextManagerAsync

from python_api.mail import EmailGenerator, Mailer
from python_api.repositories.users import UserRepository
from python_api.repositories.automated_emails import AutomatedEmails
from python_api.repositories.transactions import TransactionsRepository
from python_api.repositories.entities import EntitiesRepository
from python_api.tracking import Tracking
from python_api.utils import load_key, validate_token, ACCESS_TOKEN_EXPIRE_MINUTES


from python_api.models.users import User, UserWithInfo

from python_api.services.bucket import FileBucket
from python_api.sso.apple import AppleSSO

from .settings import Settings

from psycopg_pool import ConnectionPool, AsyncConnectionPool
import psycopg_pool

settings = Settings()

stripe.api_key = settings.stripe_secret_key

ALGORITHM = "RS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)
refresh_token = HTTPBearer(description="Refresh Token", auto_error=False)

_SETTINGS = None


async def settings():
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = Settings()
    return _SETTINGS


SettingsDep = Annotated[Settings, Depends(settings)]


async def redis(settings: SettingsDep):
    redis = await Redis.from_url(settings.redis_url)

    yield redis
    await redis.aclose()


async def mailer(settings: SettingsDep):
    mailer = Mailer(settings)
    return mailer


async def email_generator(settings: SettingsDep):
    return EmailGenerator(settings)


MailerDep = Annotated[Mailer, Depends(mailer)]
EmailGeneratorDep = Annotated[EmailGenerator, Depends(email_generator)]
RedisDep = Annotated[Redis, Depends(redis)]

CONN_POOL = None
ASYNC_CONN_POOL = None


async def conn_pool(settings: SettingsDep):
    global CONN_POOL
    if CONN_POOL is None:
        CONN_POOL = ConnectionPool(
            settings.database_dsn,
            kwargs={"row_factory": dict_row},
            min_size=1,
            max_size=15,
            open=False,
        )
        CONN_POOL.open()

    return CONN_POOL


async def async_conn_pool(settings_dep: SettingsDep):
    global ASYNC_CONN_POOL
    if ASYNC_CONN_POOL is None:
        ASYNC_CONN_POOL = psycopg_pool.AsyncConnectionPool(
            settings_dep.database_dsn,
            kwargs={"row_factory": dict_row},
            min_size=1,
            max_size=15,
            open=False,
        )
        await ASYNC_CONN_POOL.open()

    return ASYNC_CONN_POOL


ConnPoolDep = Annotated[ConnectionPool, Depends(conn_pool)]
AsyncConnPoolDep = Annotated[
    psycopg_pool.AsyncConnectionPool[AsyncConnection[DictRow]], Depends(async_conn_pool)
]


async def optional_jwt(
    response: Response,
    request: Request,
    settings: SettingsDep,
    token: Annotated[str | None, Depends(oauth2_scheme)],
):
    # print("Token from oauth2_scheme", token)
    if token == "null" or not token:
        token = request.cookies.get("accessToken", None)
        # print("Token from cookies", token)
    if not token:
        return None

    try:
        payload = validate_token(token, settings)
        # Set the access token in the response cookies
        # This is so we don't have to sign in every time we refresh the page in the docs
        response.set_cookie(
            "accessToken",
            token,
            httponly=True,
            expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=True if settings.environment in ["production", "staging"] else False,
            samesite="strict",
            domain=settings.cookie_domain,
        )

        return payload
    except ValueError as e:
        print("Probably provided a refresh token and not a access token.")
        print("Exception", e)
        traceback.print_exc()
        return None
    except (JWException, jwt.JWTExpired, InvalidJWSSignature, InvalidIDToken) as e:
        print(e)
        return None


OptionalJWTDep = Annotated[dict | None, Depends(optional_jwt)]


async def postgres_async(conn_pool: AsyncConnPoolDep, optional_jwt: OptionalJWTDep):
    async with LazyConnectionContextManagerAsync(conn_pool, optional_jwt) as conn:
        yield conn


AsyncPostgresDep = Annotated[AsyncConnection[DictRow], Depends(postgres_async)]


async def user_errors(db: AsyncPostgresDep):
    errors = UserErrors(db)
    try:
        yield errors
    finally:
        await errors.submit_all()


UserErrorsDep = Annotated[UserErrors, Depends(user_errors)]


async def automated_emails(settings: SettingsDep, postgres: AsyncPostgresDep):
    return AutomatedEmails(settings, postgres)


AutomatedEmailsDep = Annotated[AutomatedEmails, Depends(automated_emails)]


async def entities_repo(
    postgres: AsyncPostgresDep,
):
    return EntitiesRepository(postgres)


EntitiesRepositoryDep = Annotated[EntitiesRepository, Depends(entities_repo)]


async def user_repo(
    postgres: AsyncPostgresDep,
    settings: SettingsDep,
    entities: EntitiesRepositoryDep,
    x_app_platform: str | None = Header(None),
    x_app_build: str | None = Header(None),
):
    return UserRepository(x_app_platform, x_app_build, postgres, settings, entities)


UserRepositoryDep = Annotated[UserRepository, Depends(user_repo)]


async def valid_jwt(
    optional_jwt: OptionalJWTDep,
    redis: RedisDep,
    emulated_user: str | None = Query(None),
    x_emulated_user: str | None = Header(None),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    restricted_exception = HTTPException(
        status_code=status.HTTP_418_IM_A_TEAPOT,
        detail="Restricted user",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if optional_jwt is None:
        raise credentials_exception

    user = await redis.get(f"users:{optional_jwt['sub']}")
    user = User(**json.loads(user)) if user else None

    if (
        "restricted" in optional_jwt
        and optional_jwt["restricted"]
        or (user and user.restricted)
    ):
        raise restricted_exception

    if emulated_user or x_emulated_user:
        if "admin" in optional_jwt.get("roles", []):
            print("Emulating user", x_emulated_user or emulated_user)
            optional_jwt["sub"] = x_emulated_user or emulated_user

    return optional_jwt


ValidJWTDep = Annotated[dict[str, Any], Depends(valid_jwt)]


async def bucket_storage(settings: SettingsDep):
    return FileBucket(settings.bucket_storage)


BucketStorageDep = Annotated[FileBucket, Depends(bucket_storage)]


async def get_apple_keys(redis: RedisDep):
    expiration = await redis.get("apple_keys:expiration")
    if expiration:
        expiration = datetime.fromisoformat(expiration.decode("utf-8"))

    apple_keys = await redis.get("apple_keys:keys")
    if apple_keys:
        apple_keys = json.loads(apple_keys)

    if not apple_keys or not expiration or expiration <= datetime.now():
        async with httpx.AsyncClient() as client:
            try:
                keys_res = await client.get("https://appleid.apple.com/auth/keys")
                keys = keys_res.json()
                await redis.set("apple_keys:keys", json.dumps(keys["keys"]))
                await redis.set(
                    "apple_keys:expiration", str(datetime.now() + timedelta(hours=12))
                )
            except Exception:
                print("Could not get apple keys, leaving key variables as is.")

    return apple_keys


async def get_google_keys(redis: RedisDep):
    expiration = await redis.get("google_keys:expiration")
    if expiration:
        expiration = datetime.fromisoformat(expiration.decode("utf-8"))

    google_keys = await redis.get("google_keys:keys")
    if google_keys:
        google_keys = json.loads(google_keys)

    if not google_keys or not expiration or expiration <= datetime.now():
        async with httpx.AsyncClient() as client:
            try:
                keys_res = await client.get(
                    "https://www.googleapis.com/oauth2/v3/certs"
                )
                keys = keys_res.json()
                await redis.set("google_keys:keys", json.dumps(keys["keys"]))
                await redis.set(
                    "google_keys:expiration", str(datetime.now() + timedelta(hours=6))
                )
            except Exception:
                print("Could not get google keys, leaving key variables as is.")

    return google_keys


AppleKeys = Annotated[list[dict], Depends(get_apple_keys)]
GoogleKeys = Annotated[list[dict], Depends(get_google_keys)]


async def apple_sso(
    settings: SettingsDep,
    users: UserRepositoryDep,
    apple_keys: AppleKeys,
    user_errors: UserErrorsDep,
):
    return AppleSSO(settings, users, user_errors, apple_keys)


async def google_sso(settings: SettingsDep, google_keys: GoogleKeys):
    return GoogleSSO(settings, google_keys)


AppleSSODep = Annotated[AppleSSO, Depends(apple_sso)]
GoogleSSODep = Annotated[GoogleSSO, Depends(google_sso)]


async def get_current_user(
    users: UserRepositoryDep,
    valid_jwt: Annotated[dict, Depends(valid_jwt)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = valid_jwt.get("sub")
    if user_id is None:
        raise credentials_exception

    user = await users.get_user_with_info_by_id(user_id)
    if user is None:
        print("no user")
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[UserWithInfo, Depends(get_current_user)],
):
    return current_user


CurrentActiveUserDep = Annotated[UserWithInfo, Depends(get_current_active_user)]

# The reason we check redis for user roles is because jwt takes 2hrs to update user
# And we update redis when we update user.
# And the reason we don't use postgres to check is because postgres is slow
# And these checks happen every request so they need to be fast


async def admin(jwt: ValidJWTDep, redis: RedisDep):
    user = await redis.get(f"users:{jwt['sub']}")
    user = User(**json.loads(user)) if user else None
    roles = [r.value for r in user.roles] if user else []
    if roles and "admin" not in roles or "admin" not in jwt["roles"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges are required to do that.",
        )


async def editor(jwt: ValidJWTDep, redis: RedisDep):
    user = await redis.get(f"users:{jwt['sub']}")
    user = User(**json.loads(user)) if user else None
    roles = [r.value for r in user.roles] if user else []
    if (
        roles
        and ("editor" not in roles and "admin" not in roles)
        or ("editor" not in jwt["roles"] and "admin" not in jwt["roles"])
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editor or admin privileges are required to do that.",
        )


async def jwt_if_valid_subscription(jwt: ValidJWTDep):
    try:
        if "subscription" not in jwt or not jwt["subscription"]:
            return None
        else:
            expires_at = jwt["subscription"].get("expiresAt", None)
            if not expires_at:
                return None
            if datetime.fromisoformat(expires_at) < datetime.now(timezone.utc):
                return None

    except AttributeError:
        return None

    return jwt


JWTIfValidSubscriptionDep = Annotated[dict | None, Depends(jwt_if_valid_subscription)]


async def requires_sub_or_free_search(
    jwt: ValidJWTDep, has_subscription: JWTIfValidSubscriptionDep
):
    exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="subscription-required",
    )

    if "freesearcher" in jwt.get("roles", []):
        return
    if has_subscription:
        return

    raise exception


async def requires_valid_subscription(has_subscription: JWTIfValidSubscriptionDep):
    exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="subscription-required",
    )

    if has_subscription:
        return

    raise exception


ValidSubscriberDep = Annotated[User, Depends(requires_valid_subscription)]


async def transactions_repo(postgres: AsyncPostgresDep):
    return TransactionsRepository(postgres)


TransactionsRepositoryDep = Annotated[
    TransactionsRepository, Depends(transactions_repo)
]


async def tracking(redis: RedisDep, jwt: OptionalJWTDep):
    user_id = jwt.get("sub", None) if jwt else None
    yield Tracking(redis, user_id)


TrackingDep = Annotated[Tracking, Depends(tracking)]
