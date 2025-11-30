from uuid import uuid4
from . import Repository
from humps import camelize

from python_api.models.entities import Entity, EntityCreate
from python_api.models.envelopes import Envelope


class EntitiesRepository(Repository):
    def __init__(self, db):
        super().__init__(None, None)
        self.db = db

    async def create_entity(self, user_id: str, entity_create: EntityCreate) -> Entity:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO entities (id, user_id, type, name, created_at, updated_at)
                VALUES (%(id)s, %(user_id)s, %(type)s, %(name)s, NOW(), NOW())
                RETURNING id, user_id, type, name, created_at, updated_at
                """,
                {
                    "id": uuid4(),
                    "user_id": user_id,
                    "type": entity_create.type,
                    "name": entity_create.name,
                },
            )

            row = await cur.fetchone()
            return Entity(**camelize(row))

    async def get_entities_for_user(self, user_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, user_id, type, name, created_at, updated_at
                FROM entities
                WHERE user_id = %(user_id)s
                """,
                {"user_id": user_id},
            )

            entities = [Entity(**camelize(ent)) async for ent in cur]

        envelopes = await self.get_user_envelopes(user_id)
        envelopes_by_entity = {}
        for envelope in envelopes:
            envelopes_by_entity.setdefault(envelope.entity_id, []).append(envelope)

        for entity in entities:
            entity.envelopes = envelopes_by_entity.get(entity.id, [])
        return entities

    async def _ensure_master_envelopes(self, user_id: str, entity_id: str):
        envelopes = [
            Envelope(
                id=uuid4(),
                user_id=user_id,
                entity_id=entity_id,
                name="Master Income",
                type="master-income",
            ),
            Envelope(
                id=uuid4(),
                user_id=user_id,
                entity_id=entity_id,
                name="Master Expense",
                type="master-expense",
            ),
        ]

        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, type
                FROM envelopes
                WHERE user_id = %(user_id)s AND entity_id = %(entity_id)s
                """,
                {"user_id": user_id, "entity_id": entity_id},
            )

            existing_types = {row["type"] async for row in cur}
            envelopes = [env for env in envelopes if env.type not in existing_types]
            for envelope in envelopes:
                await cur.execute(
                    """
                    INSERT INTO envelopes (id, user_id, entity_id, name, type, created_at, updated_at)
                    VALUES (%(id)s, %(user_id)s, %(entity_id)s, %(name)s, %(type)s, NOW(), NOW())
                    """,
                    {
                        "id": envelope.id,
                        "user_id": envelope.user_id,
                        "entity_id": envelope.entity_id,
                        "name": envelope.name,
                        "type": envelope.type,
                    },
                )

    async def insert_envelope(self, user_id: str, entity_id: str, envelope: Envelope):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO envelopes (id, user_id, entity_id, name, type, created_at, updated_at)
                VALUES (%(id)s, %(user_id)s, %(entity_id)s, %(name)s, %(type)s, NOW(), NOW())
                RETURNING id, user_id, entity_id, name, type, created_at, updated_at
                """,
                {
                    "id": uuid4(),
                    "user_id": user_id,
                    "entity_id": entity_id,
                    "name": envelope.name,
                    "type": envelope.type,
                },
            )
            row = await cur.fetchone()
            return Envelope(**camelize(row))

    async def delete_envelope(self, user_id: str, entity_id: str, envelope_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM envelopes
                WHERE id = %(envelope_id)s AND user_id = %(user_id)s AND entity_id = %(entity_id)s
                """,
                {
                    "envelope_id": envelope_id,
                    "user_id": user_id,
                    "entity_id": entity_id,
                },
            )

    async def get_user_envelopes(self, user_id: str) -> list[Envelope]:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT e.id, e.user_id, e.entity_id, e.name, e.type, e.created_at, e.updated_at
                FROM envelopes e
                WHERE e.user_id = %(user_id)s
                """,
                {"user_id": user_id},
            )

            envelopes = [Envelope(**camelize(env)) async for env in cur]
            return envelopes
