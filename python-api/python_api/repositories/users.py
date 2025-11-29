from datetime import UTC, datetime, timedelta
import string
import uuid
import math
import random
import secrets
import base64
from humps import camelize
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from python_api.models.users import (
    AppUserUpdate,
    DbUser,
    DbUserToken,
    User,
    SsoUser,
    UnverifiedUser,
    AdminUserViewModel,
)
from python_api.models.emails import EmailType

from python_api.repositories import Repository

from python_api.settings import Settings


class UserRepository(Repository):
    def __init__(self, app_platform, app_build, db, settings: Settings):
        super().__init__(app_platform, app_build)
        self.db = db
        self.settings = settings

    @staticmethod
    def from_db_user(user: DbUser | None) -> User | None:
        return User(**user.model_dump(by_alias=True)) if user else None

    async def get_users(
        self, offset=None, limit=None, search=None
    ) -> tuple[list[User], int]:
        args = {}

        limit_sql = ""
        search_sql = ""
        if limit:
            args["limit"] = limit
            limit_sql = "LIMIT %(limit)s"
        if offset:
            args["offset"] = offset
            limit_sql += " OFFSET %(offset)s"

        if search:
            args["search"] = f"%{search}%"
            search_sql = "AND (u.email ILIKE %(search)s OR u.name ILIKE %(search)s)"

        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
            SELECT COUNT(1) as "count" FROM
            (SELECT u.id, u.email, u.email_id, u.name, u.roles, u.is_verified, u.created_at,
            u.restricted
            FROM users u
            WHERE u.deleted_at IS NULL
            {search_sql}
            GROUP BY u.id
            ) as users
            """,
                args,
            )

            count_dict = await cur.fetchone()
            user_count = count_dict["count"]

            await cur.execute(
                f"""
            SELECT u.id, u.email, u.email_id, u.name, u.roles, u.is_verified, u.created_at,
            u.restricted
            FROM users u
            WHERE u.deleted_at IS NULL
            {search_sql}
            GROUP BY u.id
            ORDER BY u.created_at DESC
            {limit_sql}
            """,
                args,
            )

            users = [User(**camelize(user)) for user in await cur.fetchall()]

            return users, user_count

    async def get_user(self, user_id: str) -> User | None:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
            SELECT u.id, u.email, u.email_id, u.name, u.roles, u.is_verified, u.restricted,
            ARRAY_AGG(su.provider) as sso_connections,
            CASE WHEN password_hash IS NOT NULL THEN true ELSE false END as has_password
            FROM users u
            LEFT JOIN sso_users su ON su.user_id = u.id
            WHERE u.id = %(user_id)s AND u.deleted_at IS NULL
            GROUP BY u.id
            """,
                {"user_id": user_id},
            )

            user = await cur.fetchone()
            if not user:
                return None

            user = User(**camelize(user))
            return user

    async def update_user_from_app(self, user_id: str, user: AppUserUpdate):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                UPDATE users
                SET
                name = %(name)s,
                updated_at = %(updated_at)s
                WHERE id = %(id)s
                """,
                {
                    "name": user.name,
                    "updated_at": datetime.now(UTC),
                    "id": user_id,
                },
            )

            return await self.get_user_by_id(user_id)

    async def update_user(self, id: str, user: AdminUserViewModel) -> User | None:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                UPDATE users
                SET
                roles = %(roles)s,
                is_verified = %(is_verified)s,
                updated_at = %(updated_at)s
                WHERE id = %(id)s
                """,
                {
                    "roles": [role.value for role in user.roles],
                    "is_verified": user.is_verified,
                    "updated_at": datetime.now(UTC),
                    "id": id,
                },
            )

            return await self.get_user(id)

    async def insert_user(self, user: DbUser):
        user.email = user.email.lower()

        async with self.db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO users
                (
                id,
                email,
                name,
                roles,
                is_verified,
                password_hash,
                created_at,
                updated_at,
                restricted,
                linked_stripe_id,
                requested_subscription,
                requested_billing_period,
                promo
                )
                VALUES
                (
                %(id)s,
                %(email)s,
                %(name)s,
                %(roles)s,
                %(is_verified)s,
                %(password_hash)s,
                %(created_at)s,
                %(updated_at)s,
                %(restricted)s,
                %(linked_stripe_id)s,
                %(requested_subscription)s,
                %(requested_billing_period)s,
                %(promo)s
                )
                RETURNING id;
                """,
                {
                    **user.model_dump(mode="json", by_alias=False),
                    "created_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                },
            )

            return (await cur.fetchone())["id"]

    async def update_password(self, user_id: str, password_hash: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                UPDATE users
                SET password_hash = %(password_hash)s, updated_at = %(updated_at)s
                WHERE id = %(user_id)s AND deleted_at IS NULL
                """,
                {
                    "password_hash": password_hash,
                    "user_id": user_id,
                    "updated_at": datetime.now(UTC),
                },
            )

    async def delete_user(self, user_id: str):
        async with self.db.cursor() as cur:
            # Delete from user_entitlements
            await cur.execute(
                """
                DELETE FROM user_entitlements
                WHERE user_id = %(user_id)s
                """,
                {"user_id": user_id},
            )

            # Delete from verification
            await cur.execute(
                """
                DELETE FROM verification
                WHERE user_id = %(user_id)s
                """,
                {"user_id": user_id},
            )

            # Delete from password_reset
            await cur.execute(
                """
                DELETE FROM password_reset
                WHERE user_id = %(user_id)s
                """,
                {"user_id": user_id},
            )

            # Delete from user_tokens
            await cur.execute(
                """
                DELETE FROM user_tokens
                WHERE user_id = %(user_id)s
                """,
                {"user_id": user_id},
            )

            # Delete from sso_users
            await cur.execute(
                """
                DELETE FROM sso_users
                WHERE user_id = %(user_id)s
                """,
                {"user_id": user_id},
            )

            # Delete from users
            await cur.execute(
                """
                UPDATE users u
                SET 
                email = %(randomstring)s,
                name = %(randomstring)s,
                password_hash = '',
                roles = '{}',
                is_verified = false,
                deleted_at = %(deleted_at)s
                WHERE id = %(user_id)s
                RETURNING id;
                """,
                {
                    "user_id": user_id,
                    "randomstring": generate_random_string(32),
                    "deleted_at": datetime.now(),
                },
            )

            return (await cur.fetchone())["id"]

    async def restrict_user(self, user_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                UPDATE users
                SET restricted = true
                WHERE id = %(user_id)s
                """,
                {"user_id": user_id},
            )

    async def un_restrict_user(self, user_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                UPDATE users
                SET restricted = false
                WHERE id = %(user_id)s
                """,
                {"user_id": user_id},
            )

    async def is_restricted(self, user_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT restricted
                FROM users
                WHERE id = %(user_id)s
                """,
                {"user_id": user_id},
            )

            return (await cur.fetchone())["restricted"]

    async def insert_sso_user(self, user: SsoUser):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO sso_users
                (id, provider, user_id)
                VALUES 
                (%(id)s, %(provider)s, %(user_id)s)
                RETURNING id;
                """,
                user.model_dump(mode="json", by_alias=False),
            )

            return (await cur.fetchone())["id"]

    async def get_sso_users(self, user_id: str) -> list[SsoUser]:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, provider, user_id
                FROM sso_users
                WHERE user_id = %s
                """,
                (user_id,),
            )

            return [SsoUser(**camelize(sso)) async for sso in cur]

    async def get_last_refresh_token(
        self, user_id: str, provider: str
    ) -> DbUserToken | None:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, refresh_token, date, provider, user_id
                FROM user_tokens
                WHERE user_id = %s AND provider = %s
                ORDER BY date DESC
                LIMIT 1
                """,
                (user_id, provider),
            )

            if not (token := await cur.fetchone()):
                return None
            return DbUserToken(**token)

    async def get_sso_user_by_id(self, sso_id: str) -> SsoUser | None:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT
                id, provider, user_id
                FROM sso_users
                WHERE id = %s
                """,
                (sso_id,),
            )

            if not (sso := await cur.fetchone()):
                return None
            return SsoUser(**camelize(sso))

    async def get_user_token_by_sso_id(self, user_id: str) -> DbUserToken | None:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT
                id, refresh_token, date, provider, user_id, sso_id
                FROM user_tokens
                WHERE sso_id = %s
                """,
                (user_id,),
            )

            if not (token := await cur.fetchone()):
                return None
            return DbUserToken(**token)

    async def get_token_provider_and_last_used(
        self, refresh_token: str
    ) -> tuple[str, int] | tuple[None, None]:
        async with self.db.cursor() as cur:
            await cur.execute(
                "SELECT provider, last_used FROM user_tokens WHERE refresh_token = %s",
                (refresh_token,),
            )
            res = await cur.fetchone()
            if not res:
                return None, None
            return res["provider"], res["last_used"]

    async def get_user_by_email(self, email: str) -> DbUser | None:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
            SELECT u.id, email, email_id, name, roles, password_hash, is_verified, restricted
            FROM users u
            WHERE email = %(email)s AND deleted_at IS NULL
            """,
                {"email": email.lower()},
            )

            if not (user := await cur.fetchone()):
                return None

        user = DbUser(**camelize(user))
        return user

    async def _get_user_by_sql_property(self, search: str, property_name: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
            SELECT
            u.id, email, email_id, name,
            roles, password_hash, is_verified,
            ARRAY_AGG(su.provider) as sso_connections
            FROM users u
            LEFT JOIN sso_users su ON su.user_id = u.id
            WHERE {property_name} = %(search)s AND deleted_at IS NULL
            GROUP BY u.id
            """,
                {"search": search},
            )

            if not (user := await cur.fetchone()):
                return None

        db_user = DbUser(**camelize(user))
        if len(db_user.sso_connections) == 1 and db_user.sso_connections[0] is None:
            db_user.sso_connections = []
        return db_user

    async def get_user_by_id(self, user_id: str) -> DbUser | None:
        user = await self._get_user_by_sql_property(user_id, "u.id")
        if not user:
            return None

        return user

    async def get_user_by_email_id(self, email_id: str) -> DbUser | None:
        return await self._get_user_by_sql_property(email_id, "u.email_id")

    async def get_user_by_sso_id(self, sso_id: str) -> DbUser | None:
        if sso_id is None:
            return None

        return await self._get_user_by_sql_property(sso_id, "su.id")

    async def get_unverified_user_by_id(self, user_id: str) -> UnverifiedUser | None:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
            SELECT u.id, u.email, u.name, v.code, is_verified, v.status, v.expires_at as code_expires_at
            FROM users u
            LEFT JOIN verification v ON u.id = v.user_id
            WHERE u.id = %(user_id)s AND deleted_at IS NULL
            """,
                {"user_id": user_id},
            )

            user = await cur.fetchone()
            if not user:
                return None

        return UnverifiedUser(**camelize(user))

    async def authenticate_user(self, email: str, password: str):
        user = await self.get_user_by_email(email)
        if not user:
            return False
        if not await self.verify_password(password, user.password_hash):
            return False
        if user.restricted:
            return False
        return user

    async def get_user_by_refresh_token(self, refresh_token) -> DbUser | None:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
            SELECT u.id, email, email_id, name, roles, password_hash,
                is_verified, restricted
            FROM users u
            INNER JOIN user_tokens ut ON u.id = ut.user_id
            WHERE ut.refresh_token = %(refresh_token)s AND u.deleted_at IS NULL
            """,
                {"refresh_token": refresh_token},
            )

            user = await cur.fetchone()
            if not user:
                return None

        user = DbUser(**camelize(user))

        return user

    async def user_refresh_token(self, email: str) -> str | None:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT ut.refresh_token FROM users u
                INNER JOIN user_tokens ut ON u.id = ut.user_id
                WHERE u.email = %(email)s AND ut.provider = %(provider)s
                AND u.deleted_at IS NULL
                """,
                {"email": email.lower(), "provider": "EXCHEQUER"},
            )

            if token := await cur.fetchone():
                return token["refresh_token"]

        user = await self.get_user_by_email(email)
        if not user:
            return None

        token = await self.insert_new_refresh_token(user.id)
        return token.refresh_token

    async def refresh_token_used(self, refresh_token: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                UPDATE user_tokens
                SET last_used = %(last_used)s
                WHERE refresh_token = %(refresh_token)s
                """,
                {
                    "last_used": int(datetime.now().timestamp()),
                    "refresh_token": refresh_token,
                },
            )

    async def update_refresh_token(self, token: DbUserToken):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                UPDATE user_tokens
                SET refresh_token = %s
                WHERE id = %s
                """,
                (token.refresh_token, token.id),
            )

    async def update_refresh_token_by_token(self, old_token: str, new_token: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                UPDATE user_tokens
                SET refresh_token = %s
                WHERE refresh_token = %s
                """,
                (new_token, old_token),
            )

    async def insert_refresh_token(self, token: DbUserToken) -> DbUserToken:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO user_tokens (id, refresh_token, date, provider, user_id, last_used)
                VALUES (%(id)s, %(refresh_token)s, %(date)s, %(provider)s, %(user_id)s, %(last_used)s)
                RETURNING id, refresh_token, date, provider, user_id, last_used;
                """,
                token.model_dump(mode="json", by_alias=False),
            )

            return DbUserToken(**await cur.fetchone())

    async def insert_new_refresh_token(
        self, user_id, provider="EXCHEQUER"
    ) -> DbUserToken:
        token_dict = {
            "id": base64.b64encode(random.randbytes(24)).decode(),
            "refresh_token": base64.b64encode(secrets.token_bytes(64)).decode(),
            "date": int(datetime.now().timestamp()),
            "provider": provider,
            "user_id": user_id,
            "last_used": int(datetime.now().timestamp()),
        }
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO user_tokens (id, refresh_token, date, provider, user_id, last_used)
                VALUES (%(id)s, %(refresh_token)s, %(date)s, %(provider)s, %(user_id)s, %(last_used)s)
                RETURNING id, refresh_token, date, provider, user_id, last_used;
                """,
                token_dict,
            )

            return DbUserToken(**await cur.fetchone())

    async def reset_password(self, email: str, password: str):
        async with self.db.cursor() as cur:
            password_hash = self.get_password_hash(password)
            await cur.execute(
                "UPDATE users SET password_hash = %s, updated_at = %s WHERE email = %s",
                (password_hash, datetime.now(UTC), email.lower()),
            )

    async def check_password_reset(self, email: str, code: str) -> bool:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT 1 FROM password_reset pr
                INNER JOIN users u ON u.id = pr.user_id
                WHERE u.email = %(email)s AND pr.code = %(code)s AND pr.expires_at > %(current)s
                """,
                {
                    "email": email.lower(),
                    "code": code,
                    "current": datetime.now().astimezone(UTC),
                },
            )

            c = await cur.fetchone()
            return bool(c)

    async def generate_password_reset(self, user_id: str) -> str | None:
        async with self.db.cursor() as cur:
            code = generate_otp(6)

            await cur.execute(
                """
                INSERT INTO password_reset
                (id, expires_at, code, user_id)
                VALUES
                (%(id)s, %(expires_at)s, %(code)s, %(user_id)s)
                """,
                {
                    "id": str(uuid.uuid4()),
                    "expires_at": datetime.now().astimezone(UTC)
                    + timedelta(minutes=15),
                    "code": code,
                    "user_id": user_id,
                },
            )

            return code

    async def generate_email_verification_code(self, user_id: str) -> str | None:
        async with self.db.cursor() as cur:
            code = generate_otp(6)

            await cur.execute(
                """
                SELECT user_id FROM verification v
                WHERE v.user_id = %(user_id)s
                """,
                {"user_id": user_id},
            )

            user_in_verification = await cur.fetchone()

            # If user Id is in verification table then just update it.
            if user_in_verification:
                await cur.execute(
                    """
                    UPDATE verification
                    SET
                    code = %(code)s,
                    expires_at = %(expires_at)s,
                    status = %(status)s
                    WHERE user_id = %(user_id)s
                    """,
                    {
                        "code": code,
                        "expires_at": datetime.now().astimezone(UTC)
                        + timedelta(minutes=15),
                        "user_id": user_id,
                        "status": False,
                    },
                )

                return code

            await cur.execute(
                """
                INSERT INTO verification
                (code, expires_at, user_id, status)
                VALUES
                (%(code)s, %(expires_at)s, %(user_id)s, %(status)s)
                """,
                {
                    "code": code,
                    "expires_at": datetime.now().astimezone(UTC)
                    + timedelta(minutes=15),
                    "user_id": user_id,
                    "status": False,
                },
            )

            return code

    async def update_user_to_verified(self, user_id):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                UPDATE verification
                SET
                code = %(code)s,
                expires_at = %(expires_at)s,
                status = %(status)s
                WHERE user_id = %(user_id)s
                """,
                {
                    "code": None,
                    "expires_at": None,
                    "user_id": user_id,
                    "status": True,
                },
            )

            await cur.execute(
                "UPDATE users SET is_verified = true WHERE id = %s", (user_id,)
            )

    async def get_subscribed_users(self, email_type: EmailType) -> list[User]:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT u.id, u.email, u.email_id, u.name, u.is_verified
                FROM users u
                JOIN user_subscriptions us ON us.user_id = u.id
                WHERE us.email_type = %(email_type)s AND u.deleted_at IS NULL
                AND u.is_verified = true AND (us.unsubscribed_at IS NULL OR us.subscribed_at > us.unsubscribed_at)
                """,
                {"email_type": email_type.value},
            )

            return [User(**camelize(user)) for user in await cur.fetchall()]

    async def is_user_subscribed(self, user_id: str, email_type: EmailType) -> bool:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT 1 FROM user_subscriptions us
                INNER JOIN users u ON u.id = us.user_id
                WHERE user_id = %(user_id)s AND email_type = %(email_type)s
                AND u.deleted_at IS NULL AND u.is_verified = true
                AND (unsubscribed_at IS NULL OR subscribed_at > unsubscribed_at)
                """,
                {"user_id": user_id, "email_type": email_type.value},
            )

            return bool(await cur.fetchone())

    async def subscribe_user(self, user_id: str, email_type: EmailType):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, subscribed_at, unsubscribed_at FROM user_subscriptions
                WHERE user_id = %(user_id)s AND email_type = %(email_type)s
                """,
                {"user_id": user_id, "email_type": email_type.value},
            )

            if not await cur.fetchone():
                await cur.execute(
                    """
                    INSERT INTO user_subscriptions
                    (user_id, email_type, subscribed_at)
                    VALUES
                    (%(user_id)s, %(email_type)s, EXTRACT(EPOCH FROM NOW()))
                    """,
                    {"user_id": user_id, "email_type": email_type.value},
                )

    # I created this function so we would not accidentally subscribe a user that has unsubscribed
    async def resubscribe_user(self, sub_id: int):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                UPDATE user_subscriptions
                SET subscribed_at = EXTRACT(EPOCH FROM NOW())
                WHERE id = %(sub_id)s
                """,
                {"sub_id": sub_id},
            )

    async def unsubscribe_user(self, user_id: str, email_type: EmailType | None):
        async with self.db.cursor() as cur:
            where_clause = "WHERE user_id = %(user_id)s"
            if email_type:
                where_clause += " AND email_type = %(email_type)s"
            await cur.execute(
                """
                UPDATE user_subscriptions
                SET unsubscribed_at = EXTRACT(EPOCH FROM NOW())
                """
                + where_clause,
                {
                    "user_id": user_id,
                    "email_type": email_type.value if email_type else None,
                },
            )

    def get_password_hash(self, password):
        return pwd_context.hash(password)

    def email_verification_email(self, code):
        return f"""If you did not request this verification code, please ignore this email.

Enter this code: {code} into your verification form. This code expires in 15 minutes"""

    async def verify_password(self, plain_password, hashed_password) -> bool:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except UnknownHashError:
            return False


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_random_string(len: int) -> str:
    res = "".join(random.choices(string.ascii_uppercase + string.digits, k=len))
    return str(res)


def generate_otp(len: int) -> str:
    digits = "0123456789"
    otp = ""

    for _ in range(len):
        otp += digits[math.floor(random.random() * 10)]

    return otp
