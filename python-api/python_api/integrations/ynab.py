from httpx import AsyncClient
from python_api.models.users import YNABIntegration
from python_api.models.ynab import (
    AccountImport,
    EnvelopeImport,
    PayeeImport,
    PlanImport,
    TransactionImport,
)
from python_api.repositories.accounts import AccountsRepository
from python_api.repositories.envelopes import EnvelopesRepository
from python_api.repositories.payees import PayeesRepository
from python_api.repositories.transactions import TransactionsRepository


class IntegrationError(Exception):
    def __init__(self, info: dict):
        self.info = info


class YNABConnector:
    def __init__(
        self,
        user_id,
        integration: YNABIntegration,
        payees: PayeesRepository,
        envelopes: EnvelopesRepository,
        accounts: AccountsRepository,
        transactions: TransactionsRepository,
    ):
        self.user_id = user_id
        self.integration = integration

        self.payees = payees
        self.envelopes = envelopes
        self.accounts = accounts
        self.transactions = transactions

    def _client(self):
        headers = {}

        if self.integration.token:
            headers["Authorization"] = f"Bearer {self.integration.token}"

        return AsyncClient(base_url="https://api.ynab.com/v1", headers=headers)

    async def validate_connection(self) -> bool:
        async with self._client() as client:
            res = await client.get("/budgets")
            if res.status_code != 200:
                raise IntegrationError(res.json())

        return True

    async def get_plans(self) -> list[PlanImport]:
        async with self._client() as client:
            res = await client.get("/budgets")
            if res.status_code != 200:
                raise IntegrationError(res.json())

            data = res.json()

        plans = [
            PlanImport(
                name=budget["name"],
                currency_code=budget["currency_format"]["iso_code"],
                imported_document=budget,
                import_source="ynab",
                import_id=budget["id"],
                import_revision=None,
            )
            for budget in data["data"]["budgets"]
        ]

        return plans

    async def get_categories(
        self, plan_id: str, last_server_knowledge: int | None
    ) -> list:
        async with self._client() as client:
            res = await client.get(
                f"/budgets/{plan_id}/categories",
                params={
                    "last_knowledge_of_server": last_server_knowledge,
                }
                if last_server_knowledge is not None
                else None,
            )

            if res.status_code != 200:
                raise IntegrationError(res.json())

            data = res.json()

        server_knowledge = data["data"]["server_knowledge"]

        envelope_imports = []
        for category_group in data["data"]["category_groups"]:
            for category in category_group["categories"]:
                envelope_import = EnvelopeImport(
                    name=category["name"],
                    hidden=category["hidden"],
                    imported_document=category,
                    import_revision=server_knowledge,
                    import_source="ynab",
                    import_id=category["id"],
                )

                envelope_imports.append(envelope_import)

        return envelope_imports

    async def get_accounts(
        self, plan_id: str, last_server_knowledge: int | None
    ) -> list:
        async with self._client() as client:
            res = await client.get(
                f"/budgets/{plan_id}/accounts",
                params={
                    "last_knowledge_of_server": last_server_knowledge,
                }
                if last_server_knowledge is not None
                else None,
            )

            if res.status_code != 200:
                raise IntegrationError(res.json())

            data = res.json()

        server_knowledge = data["data"]["server_knowledge"]

        account_imports = []
        for account in data["data"]["accounts"]:
            account_import = AccountImport(
                name=account["name"],
                type=account["type"],
                closed=account["closed"],
                imported_document=account,
                import_revision=server_knowledge,
                import_source="ynab",
                import_id=account["id"],
            )

            account_imports.append(account_import)

        return account_imports

    async def get_payees(
        self, plan_id: str, last_server_knowledge: int | None
    ) -> list[PayeeImport]:
        async with self._client() as client:
            res = await client.get(
                f"/budgets/{plan_id}/payees",
                params={
                    "last_knowledge_of_server": last_server_knowledge,
                }
                if last_server_knowledge is not None
                else None,
            )

            if res.status_code != 200:
                raise IntegrationError(res.json())

            data = res.json()

        server_knowledge = data["data"]["server_knowledge"]

        payees = [
            PayeeImport(
                name=payee["name"],
                transfer_account_id=payee.get("transfer_account_id"),
                imported_document=payee,
                import_revision=server_knowledge,
                import_source="ynab",
                import_id=payee["id"],
            )
            for payee in data["data"]["payees"]
        ]

        return payees

    async def get_transactions(
        self, plan_id: str, last_server_knowledge: int | None
    ) -> list:
        async with self._client() as client:
            res = await client.get(
                f"/budgets/{plan_id}/transactions",
                params={
                    "last_knowledge_of_server": last_server_knowledge,
                }
                if last_server_knowledge is not None
                else None,
            )

            if res.status_code != 200:
                raise IntegrationError(res.json())

            data = res.json()

        server_knowledge = data["data"]["server_knowledge"]

        transactions = []
        for transaction in data["data"]["transactions"]:
            transaction_import = TransactionImport(
                id=transaction["id"],
                date=transaction["date"],
                amount=transaction["amount"],
                account_id=transaction["account_id"],
                payee_id=transaction.get("payee_id"),
                category_id=transaction.get("category_id"),
                transfer_account_id=transaction.get("transfer_account_id"),
                transfer_transaction_id=transaction.get("transfer_transaction_id"),
                matched_transaction_id=transaction.get("matched_transaction_id"),
                description=transaction.get("memo"),
                cleared=transaction["cleared"],
                approved=transaction["approved"],
                imported_document=transaction,
                import_revision=server_knowledge,
                import_source="ynab",
                import_id=transaction["id"],
            )

            transactions.append(transaction_import)
            for sub in transaction.get("subtransactions", []):
                sub_transaction_import = TransactionImport(
                    id=sub["id"],
                    date=transaction["date"],
                    amount=sub["amount"],
                    account_id=transaction["account_id"],
                    payee_id=sub.get("payee_id"),
                    category_id=sub.get("category_id"),
                    transfer_account_id=sub.get("transfer_account_id"),
                    transfer_transaction_id=sub.get("transfer_transaction_id"),
                    parent_transaction_id=sub.get("transaction_id"),
                    description=sub.get("memo"),
                    cleared=transaction["cleared"],
                    approved=transaction["approved"],
                    imported_document=sub,
                    import_revision=server_knowledge,
                    import_source="ynab",
                    import_id=sub["id"],
                )

                transactions.append(sub_transaction_import)

        return transactions

    async def import_payees(self, ynab_plan_id: str, full_reimport: bool = False):
        last_server_knowledge = None
        if not full_reimport:
            last_server_knowledge = await self.payees.get_last_import_revision(
                self.user_id, "ynab"
            )

        payees = await self.get_payees(ynab_plan_id, last_server_knowledge)

        for payee in payees:
            await self.payees.import_payee(self.user_id, payee)

        return (
            len(payees),
            last_server_knowledge,
            payees[-1].import_revision if payees else last_server_knowledge,
        )

    async def import_envelopes(self, ynab_plan_id: str, full_reimport: bool = False):
        last_server_knowledge = None
        if not full_reimport:
            last_server_knowledge = await self.envelopes.get_last_import_revision(
                self.user_id, "ynab"
            )

        categories = await self.get_categories(ynab_plan_id, last_server_knowledge)

        for category in categories:
            await self.envelopes.import_envelope(self.user_id, category)

        return (
            len(categories),
            last_server_knowledge,
            categories[-1].import_revision if categories else last_server_knowledge,
        )

    async def import_accounts(self, ynab_plan_id: str, full_reimport: bool = False):
        last_server_knowledge = None
        if not full_reimport:
            last_server_knowledge = await self.accounts.get_last_import_revision(
                self.user_id, "ynab"
            )

        accounts = await self.get_accounts(ynab_plan_id, last_server_knowledge)
        for account in accounts:
            await self.accounts.import_account(self.user_id, account)

        return (
            len(accounts),
            last_server_knowledge,
            accounts[-1].import_revision if accounts else last_server_knowledge,
        )

    async def import_transactions(self, ynab_plan_id: str, full_reimport: bool = False):
        last_server_knowledge = None
        if not full_reimport:
            last_server_knowledge = await self.transactions.get_last_import_revision(
                self.user_id, "ynab"
            )

        transactions = await self.get_transactions(ynab_plan_id, last_server_knowledge)

        for transaction in transactions:
            await self.transactions.import_transaction(self.user_id, transaction)

        await self.transactions.finalize_transaction_imports(self.user_id, "ynab")

        return (
            len(transactions),
            last_server_knowledge,
            transactions[-1].import_revision if transactions else last_server_knowledge,
        )
