from fastapi import APIRouter

from python_api.dependencies import YNABConnectorDep
from python_api.integrations.ynab import YNABConnector
from python_api.models.ynab import YNABPlan

router = APIRouter(prefix="/ynab", tags=["YNAB"])


@router.get("/plans")
async def get_ynab_plans(ynab: YNABConnectorDep) -> list[YNABPlan]:
    return await ynab.get_plans()
