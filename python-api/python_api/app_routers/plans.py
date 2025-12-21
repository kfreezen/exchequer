from fastapi import APIRouter

from python_api.dependencies import (
    PlansRepositoryDep,
    UserRepositoryDep,
    ValidJWTDep,
)

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.get("")
async def get_user_plans(
    plans_repo: PlansRepositoryDep,
    valid_jwt: ValidJWTDep,
):
    return await plans_repo.get_user_plans(valid_jwt["sub"])
