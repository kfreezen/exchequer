from fastapi import APIRouter, HTTPException

from python_api.models import CamelModel
from python_api.models.transactions import TransactionCreate, TransactionUpdate
from python_api.dependencies import (
    TransactionsRepositoryDep,
    ValidJWTDep,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("")
async def create_transaction(
    body: TransactionCreate,
    transactions_repo: TransactionsRepositoryDep,
    valid_jwt: ValidJWTDep,
):
    created = await transactions_repo.create_transaction(
        user_id=valid_jwt["sub"],
        amount=body.amount,
        date=body.date,
        description=body.description,
        envelope_id=body.envelope_id,
        entity_id=body.entity_id,
    )
    return created


@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    body: TransactionUpdate,
    transactions_repo: TransactionsRepositoryDep,
    valid_jwt: ValidJWTDep,
):
    print("Updating transaction:", transaction_id, body)
    updated = await transactions_repo.update_transaction(
        user_id=valid_jwt["sub"],
        transaction_id=transaction_id,
        amount=body.amount,
        date=body.date,
        description=body.description,
        envelope_id=body.envelope_id,
        entity_id=body.entity_id,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return updated
