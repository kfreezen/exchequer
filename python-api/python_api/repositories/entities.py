from uuid import uuid4
from . import Repository
from humps import camelize

from python_api.models.entities import Entity, EntityCreate, EntityType
from python_api.models.envelopes import Envelope


class EntitiesRepository(Repository):
    def __init__(self, db):
        super().__init__(None, None)
        self.db = db

    async def create_default_entities(self, user_id: str):
        default_entities = [
            EntityCreate(type=EntityType.PERSONAL, name="Personal"),
            EntityCreate(type=EntityType.BUSINESS, name="Business"),
        ]

        entities = []
        for entity_create in default_entities:
            entity = await self.create_entity(user_id, entity_create)
            entities.append(entity)

        return entities

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
