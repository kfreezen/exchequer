from uuid import uuid4
from humps import camelize
from python_api.models.plans import Plan
from python_api.models.ynab import YNABPlan
from . import Repository


class PayeesRepository(Repository):
    def __init__(self, db):
        super().__init__(None, None)
        self.db = db

    async def import_ynab_payee(self, user_id: str, ynab_payee: YNABPayee):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO payees (id, import_id, user_id, name, created_at, updated_at, imported_document, import_revision)
                VALUES (%(id)s, %(import_id)s, %(user_id)s, %(name)s, NOW(), NOW(), %(imported_document)s, %(import_revision)s)
                ON CONFLICT (import_id) DO NOTHING
                RETURNING id, user_id, name, created_at, updated_at
                """,
                {
                    "id": uuid4(),
                    "import_id": ynab_payee.id,
                    "user_id": user_id,
                    "name": ynab_payee.name,
                    "imported_document": ynab_payee.imported_document,
                    "import_revision": ynab_payee.import_revision,
                },
            )

            row = await cur.fetchone()
            if not row or not row["id"]:
                return await self.get_payee_by_import_id(ynab_payee.id)

            return Payee.model_validate(camelize(row))

    FIELDS = [
        "id",
        "name",
        "created_at",
        "updated_at",
        "import_id",
    ]

    FIELD_STRING = ", ".join(FIELDS)

    async def get_payee_by_import_id(self, import_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {self.FIELD_STRING}
                FROM payees
                WHERE import_id = %(import_id)s
                """,
                {"import_id": import_id},
            )

            row = await cur.fetchone()
            if row:
                return Payee.model_validate(camelize(row))
            return None

    async def get_payee_by_id(self, payee_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {self.FIELD_STRING}
                FROM payees
                WHERE id = %(payee_id)s
                """,
                {"payee_id": payee_id},
            )

            row = await cur.fetchone()
            if row:
                return Payee.model_validate(camelize(row))
            return None
