import json
from uuid import uuid4
from fastapi import HTTPException
from humps import camelize
from python_api.models.envelopes import Envelope, EnvelopeWithTransactionCounts
from python_api.models.ynab import EnvelopeImport
from . import Repository


class EnvelopesRepository(Repository):
    def __init__(self, db):
        super().__init__(None, None)
        self.db = db

    async def get_last_import_revision(self, user_id, import_source: str) -> int | None:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT MAX(import_revision) AS last_import_revision
                FROM envelopes
                WHERE import_source = %(import_source)s AND
                        user_id = %(user_id)s
                """,
                {"import_source": import_source, "user_id": user_id},
            )

            row = await cur.fetchone()
            if row and row["last_import_revision"] is not None:
                return row["last_import_revision"]

            return None

    async def import_envelope(
        self, user_id: str, category: EnvelopeImport
    ) -> Envelope | None:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO envelopes (id, import_id, user_id, name, created_at, updated_at, imported_document, import_revision, import_source)
                VALUES (%(id)s, %(import_id)s, %(user_id)s, %(name)s, NOW(), NOW(), %(imported_document)s, %(import_revision)s, %(import_source)s)
                ON CONFLICT (import_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    updated_at = NOW(),
                    imported_document = EXCLUDED.imported_document,
                    import_revision = EXCLUDED.import_revision,
                    import_source = EXCLUDED.import_source
                RETURNING id, user_id, name, created_at, updated_at
                """,
                {
                    "id": uuid4(),
                    "import_id": category.import_id,
                    "user_id": user_id,
                    "name": category.name,
                    "imported_document": json.dumps(category.imported_document),
                    "import_revision": category.import_revision,
                    "import_source": category.import_source,
                },
            )

            row = await cur.fetchone()
            if not row or not row["id"]:
                return await self.get_envelope_by_import_id(category.import_id)

            return Envelope.model_validate(camelize(row))

    FIELDS = [
        "id",
        "name",
        "created_at",
        "updated_at",
        "import_id",
    ]

    FIELD_STRING = ", ".join(FIELDS)

    async def get_envelope_by_import_id(self, import_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {self.FIELD_STRING}
                FROM envelopes
                WHERE import_id = %(import_id)s
                """,
                {"import_id": import_id},
            )

            row = await cur.fetchone()
            if row:
                return Envelope.model_validate(camelize(row))

            return None

    async def get_envelope_by_id(self, user_id, envelope_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {self.FIELD_STRING}
                FROM envelopes
                WHERE id = %(envelope_id)s AND user_id = %(user_id)s
                """,
                {"envelope_id": envelope_id, "user_id": user_id},
            )

            row = await cur.fetchone()
            if row:
                return Envelope.model_validate(camelize(row))
            return None

    async def get_user_envelopes(self, user_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT e.id, e.entity_id, e.name, e.created_at, e.updated_at
                FROM envelopes e
                JOIN entities en ON e.entity_id = en.id
                WHERE en.user_id = %(user_id)s
                """,
                {"user_id": user_id},
            )

            envelopes = [Envelope(**camelize(env)) async for env in cur]
            return envelopes

    async def insert_envelope(self, user_id, envelope: Envelope) -> Envelope:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO envelopes (id, user_id, entity_id, name, created_at, updated_at)
                VALUES (%(id)s, %(user_id)s, %(entity_id)s, %(name)s, NOW(), NOW())
                RETURNING id, entity_id, name, created_at, updated_at
                """,
                {
                    "id": envelope.id,
                    "user_id": user_id,
                    "entity_id": envelope.entity_id,
                    "name": envelope.name,
                },
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(400, detail="Failed to insert envelope")

            return Envelope.model_validate(camelize(row))

    async def update_envelope(self, envelope: Envelope) -> Envelope:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                UPDATE envelopes
                SET name = %(name)s,
                    updated_at = NOW()
                WHERE id = %(id)s
                RETURNING id, entity_id, name, created_at, updated_at
                """,
                {
                    "id": envelope.id,
                    "name": envelope.name,
                },
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(400, detail="Failed to update envelope")

            return Envelope.model_validate(camelize(row))

    async def delete_envelope(self, user_id: str, entity_id: str, envelope_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM envelopes
                WHERE id = %(envelope_id)s AND entity_id = %(entity_id)s AND user_id = %(user_id)s
                """,
                {
                    "envelope_id": envelope_id,
                    "user_id": user_id,
                    "entity_id": entity_id,
                },
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(404, detail="Envelope not found")

            return True

    async def get_unassigned_envelopes(self, user_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT e.id, e.entity_id, e.name, e.created_at, e.updated_at
                FROM envelopes e
                WHERE e.entity_id IS NULL
                """,
                {"user_id": user_id},
            )

            envelopes = [Envelope(**camelize(env)) async for env in cur]
            return envelopes

    async def assign_envelopes_to_entity(
        self, user_id: str, entity_id: str, envelope_ids: list[str]
    ):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                UPDATE envelopes
                SET entity_id = %(entity_id)s,
                    updated_at = NOW()
                WHERE id = ANY(%(envelope_ids)s) AND entity_id IS NULL
                AND user_id = %(user_id)s
                RETURNING id, entity_id, name, created_at, updated_at
                """,
                {
                    "entity_id": entity_id,
                    "envelope_ids": envelope_ids,
                    "user_id": user_id,
                },
            )

    async def assign_envelope_transactions_to_entity(
        self, user_id: str, entity_id: str, envelope_ids: list[str]
    ):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                UPDATE transactions
                SET entity_id = %(entity_id)s,
                    updated_at = NOW()
                WHERE envelope_id = ANY(%(envelope_ids)s) AND entity_id IS NULL
                AND user_id = %(user_id)s
                """,
                {
                    "entity_id": entity_id,
                    "envelope_ids": envelope_ids,
                    "user_id": user_id,
                },
            )

    async def get_unassigned_envelope_transactions(self, user_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT e.id, e.entity_id, e.name, e.created_at, e.updated_at,
                    COUNT(et.id) AS unassigned_transaction_count
                FROM envelopes e
                LEFT JOIN transactions et ON e.id = et.envelope_id AND et.entity_id IS NULL
                WHERE e.user_id = %(user_id)s
                GROUP BY e.id, e.entity_id, e.name, e.created_at, e.updated_at
                HAVING COUNT(et.id) > 0
                """,
                {"user_id": user_id},
            )

            envelopes = []
            async for row in cur:
                envelope_data = camelize(row)
                envelope = EnvelopeWithTransactionCounts.model_validate(envelope_data)
                envelope.unassigned_transaction_count = row[
                    "unassigned_transaction_count"
                ]
                envelopes.append(envelope)

            return envelopes
