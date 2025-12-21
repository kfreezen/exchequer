from fastapi import APIRouter

from python_api.dependencies import (
    PlansRepositoryDep,
    UserRepositoryDep,
    ValidJWTDep,
    YNABConnectorDep,
)
from python_api.integrations.ynab import YNABConnector
from python_api.models import CamelModel
from python_api.models.ynab import YNABPlan
from python_api.repositories.users import UserRepository

router = APIRouter(prefix="/ynab", tags=["YNAB"])


@router.get("/plans")
async def get_ynab_plans(ynab: YNABConnectorDep) -> list[YNABPlan]:
    return await ynab.get_plans()


class PlanImport(CamelModel):
    plans: list[YNABPlan]


@router.post("/import/plans")
async def import_ynab_data(
    ynab: YNABConnectorDep,
    plans: PlanImport,
    plans_repo: PlansRepositoryDep,
    users: UserRepositoryDep,
    valid_jwt: ValidJWTDep,
):
    for plan in plans.plans:
        await plans_repo.import_ynab_plan(valid_jwt["sub"], plan)
