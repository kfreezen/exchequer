from uuid import uuid4
from humps import camelize
from python_api.models.plans import Plan
from python_api.models.ynab import YNABPlan
from . import Repository


class PlansRepository(Repository):
    def __init__(self, db):
        super().__init__(None, None)
        self.db = db

    async def import_ynab_plan(self, user_id: str, ynab_plan: YNABPlan):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO plans (id, import_id, user_id, name, currency_code, created_at, updated_at)
                VALUES (%(id)s, %(import_id)s, %(user_id)s, %(name)s, %(currency_code)s, NOW(), NOW())
                ON CONFLICT (import_id) DO NOTHING
                RETURNING id, user_id, name, currency_code, created_at, updated_at
                """,
                {
                    "id": uuid4(),
                    "import_id": ynab_plan.id,
                    "user_id": user_id,
                    "name": ynab_plan.name,
                    "currency_code": ynab_plan.currency_code,
                },
            )

            row = await cur.fetchone()
            if not row or not row["id"]:
                return await self.get_plan_by_import_id(ynab_plan.id)

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
