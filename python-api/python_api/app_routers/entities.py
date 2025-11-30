from fastapi import APIRouter

from python_api.dependencies import ValidJWTDep, EntitiesRepositoryDep
from python_api.models.entities import EntityCreate
from python_api.models.envelopes import EnvelopeCreate

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("")
async def list_entities(jwt: ValidJWTDep, entities: EntitiesRepositoryDep):
    return await entities.get_entities_for_user(jwt["sub"])


@router.post("")
async def create_entity(
    jwt: ValidJWTDep,
    entities: EntitiesRepositoryDep,
    entity_create: EntityCreate,
):
    return await entities.create_entity(jwt["sub"], entity_create)


@router.post("/{entity_id}/envelopes")
async def create_entity_envelope(
    jwt: ValidJWTDep,
    entities: EntitiesRepositoryDep,
    entity_id: str,
    envelope: EnvelopeCreate,
):
    return await entities.insert_envelope(jwt["sub"], entity_id, envelope)


@router.delete("/{entity_id}/envelopes/{envelope_id}")
async def delete_entity_envelope(
    jwt: ValidJWTDep,
    entities: EntitiesRepositoryDep,
    entity_id: str,
    envelope_id: str,
):
    return await entities.delete_envelope(jwt["sub"], entity_id, envelope_id)
