from fastapi import APIRouter, HTTPException

from python_api.models import CamelModel
from python_api.dependencies import (
    TransactionsRepositoryDep,
    ValidJWTDep,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])
