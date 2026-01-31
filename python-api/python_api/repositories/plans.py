from uuid import uuid4
from humps import camelize
from python_api.models.plans import Plan
from python_api.models.ynab import PlanImport
from . import Repository


class PlansRepository(Repository):
    def __init__(self, db):
        super().__init__(None, None)
        self.db = db

    async def import_plan(self, user_id: str, plan: PlanImport):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO plans (id, import_id, user_id, name, currency_code, created_at, updated_at, imported_document, import_source)
                VALUES (%(id)s, %(import_id)s, %(user_id)s, %(name)s, %(currency_code)s, NOW(), NOW(), %(imported_document)s, %(import_source)s)
                ON CONFLICT (import_id) DO NOTHING
                RETURNING id, user_id, name, currency_code, created_at, updated_at
                """,
                {
                    "id": uuid4(),
                    "import_id": plan.import_id,
                    "user_id": user_id,
                    "name": plan.name,
                    "currency_code": plan.currency_code,
                    "imported_document": plan.model_dump_json(),
                    "import_source": plan.import_source,
                },
            )

            row = await cur.fetchone()
            if not row or not row["id"]:
                return await self.get_plan_by_import_id(plan.import_id)

            return Plan.model_validate(camelize(row))

    FIELDS = [
        "id",
        "name",
        "currency_code",
        "created_at",
        "updated_at",
        "import_id",
    ]

    FIELD_STRING = ", ".join(FIELDS)

    async def get_plan_by_import_id(self, import_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {self.FIELD_STRING}
                FROM plans
                WHERE import_id = %(import_id)s
                """,
                {"import_id": import_id},
            )

            row = await cur.fetchone()
            if row:
                return Plan.model_validate(camelize(row))
            return None

    async def get_plan_by_id(self, plan_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {self.FIELD_STRING}
                FROM plans
                WHERE id = %(plan_id)s
                """,
                {"plan_id": plan_id},
            )

            row = await cur.fetchone()
            if row:
                return Plan.model_validate(camelize(row))
            return None

    async def get_user_plans(self, user_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, name, currency_code, created_at, updated_at, import_id
                FROM plans
                WHERE user_id = %(user_id)s
                """,
                {"user_id": user_id},
            )

            plans = [Plan.model_validate(camelize(plan)) async for plan in cur]
            return plans
