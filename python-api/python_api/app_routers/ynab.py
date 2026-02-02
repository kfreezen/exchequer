from fastapi import APIRouter

from python_api.dependencies import (
    PlansRepositoryDep,
    UserRepositoryDep,
    ValidJWTDep,
    YNABConnectorDep,
)
from python_api.integrations.ynab import YNABConnector
from python_api.models import CamelModel
from python_api.models.ynab import PlanImport
from python_api.repositories.users import UserRepository

router = APIRouter(prefix="/ynab", tags=["YNAB"])


@router.get("/plans")
async def get_ynab_plans(ynab: YNABConnectorDep) -> list[PlanImport]:
    return await ynab.get_plans()


class PlanImportList(CamelModel):
    plans: list[PlanImport]


@router.post("/import/plans")
async def import_ynab_plans(
    ynab: YNABConnectorDep,
    plans: PlanImportList,
    plans_repo: PlansRepositoryDep,
    users: UserRepositoryDep,
    valid_jwt: ValidJWTDep,
):
    for plan in plans.plans:
        await plans_repo.import_plan(valid_jwt["sub"], plan)


@router.post("/import/payees")
async def import_ynab_payees(
    ynab: YNABConnectorDep,
    plans_repo: PlansRepositoryDep,
    valid_jwt: ValidJWTDep,
    full: bool = False,
):
    plans = await plans_repo.get_user_plans(valid_jwt["sub"])

    results = {}

    for plan in plans:
        payees_imported, first_knowledge, last_knowledge = await ynab.import_payees(
            str(plan.import_id), full_reimport=full
        )

        results[plan.id] = {
            "payeesImported": payees_imported,
            "serverKnowledge": first_knowledge,
            "lastServerKnowledge": last_knowledge,
        }

        print(
            f"Imported {payees_imported} payees for plan {plan.name} (server knowledge: {first_knowledge}->{last_knowledge})"
        )

    return results


@router.post("/import/categories")
async def import_ynab_categories(
    ynab: YNABConnectorDep,
    plans_repo: PlansRepositoryDep,
    valid_jwt: ValidJWTDep,
    full: bool = False,
):
    plans = await plans_repo.get_user_plans(valid_jwt["sub"])

    results = {}

    for plan in plans:
        (
            categories_imported,
            first_knowledge,
            last_knowledge,
        ) = await ynab.import_envelopes(str(plan.import_id), full_reimport=full)

        results[plan.id] = {
            "categoriesImported": categories_imported,
            "serverKnowledge": first_knowledge,
            "lastServerKnowledge": last_knowledge,
        }

        print(
            f"Imported {categories_imported} categories for plan {plan.name} (server knowledge: {first_knowledge}->{last_knowledge})"
        )

    return results


@router.post("/import/accounts")
async def import_ynab_accounts(
    ynab: YNABConnectorDep,
    plans_repo: PlansRepositoryDep,
    valid_jwt: ValidJWTDep,
    full: bool = False,
):
    plans = await plans_repo.get_user_plans(valid_jwt["sub"])

    results = {}

    for plan in plans:
        (
            accounts_imported,
            first_knowledge,
            last_knowledge,
        ) = await ynab.import_accounts(str(plan.import_id), full_reimport=full)

        results[plan.id] = {
            "accountsImported": accounts_imported,
            "serverKnowledge": first_knowledge,
            "lastServerKnowledge": last_knowledge,
        }

        print(
            f"Imported {accounts_imported} accounts for plan {plan.name} (server knowledge: {first_knowledge}->{last_knowledge})"
        )

    return results


@router.post("/import/transactions")
async def import_ynab_transactions(
    ynab: YNABConnectorDep,
    plans_repo: PlansRepositoryDep,
    valid_jwt: ValidJWTDep,
    full: bool = False,
):
    plans = await plans_repo.get_user_plans(valid_jwt["sub"])

    results = {}

    for plan in plans:
        (
            transactions_imported,
            first_knowledge,
            last_knowledge,
        ) = await ynab.import_transactions(str(plan.import_id), full_reimport=full)

        results[plan.id] = {
            "transactionsImported": transactions_imported,
            "serverKnowledge": first_knowledge,
            "lastServerKnowledge": last_knowledge,
        }

        print(
            f"Imported {transactions_imported} transactions for plan {plan.name} (server knowledge: {first_knowledge}->{last_knowledge})"
        )

    return results
