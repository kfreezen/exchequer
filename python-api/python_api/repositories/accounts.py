import json
from uuid import uuid4
from humps import camelize
from python_api.models.accounts import Account
from python_api.models.ynab import AccountImport
from . import Repository


class AccountsRepository(Repository):
    def __init__(self, db):
        super().__init__(None, None)
        self.db = db

    async def import_account(
        self, user_id: str, account: AccountImport
    ) -> Account | None:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO accounts (id, import_id, user_id, name, type, closed, created_at, updated_at, imported_document, import_revision, import_source)
                VALUES (%(id)s, %(import_id)s, %(user_id)s, %(name)s, %(type)s, %(closed)s, NOW(), NOW(), %(imported_document)s, %(import_revision)s, %(import_source)s)
                ON CONFLICT (import_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    type = EXCLUDED.type,
                    updated_at = NOW(),
                    closed = EXCLUDED.closed,
                    imported_document = EXCLUDED.imported_document,
                    import_revision = EXCLUDED.import_revision,
                    import_source = EXCLUDED.import_source
                RETURNING id, user_id, name, type, created_at, updated_at, closed
                """,
                {
                    "id": uuid4(),
                    "user_id": user_id,
                    "name": account.name,
                    "type": account.type,
                    "closed": account.closed,
                    "imported_document": json.dumps(account.imported_document),
                    "import_revision": account.import_revision,
                    "import_source": account.import_source,
                    "import_id": account.import_id,
                },
            )

            row = await cur.fetchone()
            if not row or not row["id"]:
                return await self.get_account_by_import_id(account.import_id)

            return Account.model_validate(camelize(row))

    FIELDS = [
        "id",
        "user_id",
        "name",
        "type",
        "closed",
        "created_at",
        "updated_at",
        "import_id",
    ]

    FIELD_STRING = ", ".join(FIELDS)

    async def get_account_by_import_id(self, import_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {self.FIELD_STRING}
                FROM accounts
                WHERE import_id = %(import_id)s
                """,
                {"import_id": import_id},
            )

            row = await cur.fetchone()
            if row:
                return Account.model_validate(camelize(row))

    async def get_account_by_id(self, account_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {self.FIELD_STRING}
                FROM accounts
                WHERE id = %(account_id)s
                """,
                {"account_id": account_id},
            )

            row = await cur.fetchone()
            if row:
                return Account.model_validate(camelize(row))

    async def get_user_accounts(self, user_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {self.FIELD_STRING}
                FROM accounts
                WHERE user_id = %(user_id)s
                """,
                {"user_id": user_id},
            )

            rows = await cur.fetchall()
            return [Account.model_validate(camelize(row)) for row in rows]

    async def get_last_import_revision(
        self, user_id: str, import_source: str
    ) -> int | None:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT MAX(import_revision) AS last_import_revision
                FROM accounts
                WHERE user_id = %(user_id)s AND import_source = %(import_source)s
                """,
                {"user_id": user_id, "import_source": import_source},
            )

            row = await cur.fetchone()
            if row and row["last_import_revision"] is not None:
                return row["last_import_revision"]
            return None
