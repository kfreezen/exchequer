from fastapi import HTTPException, APIRouter

from python_api.dependencies import (
    EnvelopesRepositoryDep,
    TransactionsRepositoryDep,
    ValidJWTDep,
)
from python_api.models import CamelModel
from python_api.models.envelopes import EnvelopeWithTransactions

router = APIRouter(prefix="/envelopes", tags=["Envelopes"])


@router.get("")
async def get_all_envelopes(
    envelopes_repo: EnvelopesRepositoryDep, valid_jwt: ValidJWTDep
):
    envelopes = await envelopes_repo.get_all_user_envelopes(valid_jwt["sub"])
    return envelopes


@router.get("/unassigned")
async def get_unassigned_envelopes(
    envelopes_repo: EnvelopesRepositoryDep, valid_jwt: ValidJWTDep
):
    envelopes = await envelopes_repo.get_unassigned_envelopes(valid_jwt["sub"])
    return envelopes


class AssignEnvelopesRequest(CamelModel):
    entity_id: str
    envelope_ids: list[str]


@router.post("/assign")
async def assign_envelopes_to_entity(
    body: AssignEnvelopesRequest,
    envelopes_repo: EnvelopesRepositoryDep,
    valid_jwt: ValidJWTDep,
):
    await envelopes_repo.assign_envelopes_to_entity(
        valid_jwt["sub"], body.entity_id, body.envelope_ids
    )

    return await envelopes_repo.get_unassigned_envelopes(valid_jwt["sub"])


@router.post("/assign-transactions")
async def assign_envelopes_transactions_to_entity(
    body: AssignEnvelopesRequest,
    envelopes_repo: EnvelopesRepositoryDep,
    valid_jwt: ValidJWTDep,
):
    await envelopes_repo.assign_envelope_transactions_to_entity(
        valid_jwt["sub"], body.entity_id, body.envelope_ids
    )

    return await envelopes_repo.get_unassigned_envelope_transactions(valid_jwt["sub"])


@router.get("/unassigned-transactions")
async def get_unassigned_envelope_transaction_counts(
    envelopes_repo: EnvelopesRepositoryDep, valid_jwt: ValidJWTDep
):
    envelopes = await envelopes_repo.get_unassigned_envelope_transactions(
        valid_jwt["sub"]
    )
    return envelopes


@router.get("/{envelope_id}")
async def get_envelope_by_id(
    envelope_id: str,
    envelopes_repo: EnvelopesRepositoryDep,
    transactions_repo: TransactionsRepositoryDep,
    valid_jwt: ValidJWTDep,
):
    envelope = await envelopes_repo.get_envelope_by_id(valid_jwt["sub"], envelope_id)
    if not envelope:
        raise HTTPException(status_code=404, detail="Envelope not found")

    transactions = await transactions_repo.get_transactions_by_envelope_id(
        valid_jwt["sub"], envelope_id
    )

    envelope_with_transactions = EnvelopeWithTransactions(
        **envelope.model_dump(), transactions=transactions
    )
    return envelope_with_transactions


class AssignTransactionsRequest(CamelModel):
    entity_id: str
    transaction_ids: list[str]


@router.post("/{envelope_id}/assign-transactions")
async def assign_transactions_to_entity(
    transactions_repo: TransactionsRepositoryDep,
    valid_jwt: ValidJWTDep,
    envelope_id: str,
    body: AssignTransactionsRequest,
):
    await transactions_repo.assign_transactions_to_entity(
        valid_jwt["sub"],
        body.entity_id,
        body.transaction_ids,
    )

    transactions = await transactions_repo.get_transactions_by_envelope_id(
        valid_jwt["sub"], envelope_id
    )
    return transactions
