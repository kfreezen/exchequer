from httpx import AsyncClient
from python_api.models.users import YNABIntegration
from python_api.models.ynab import YNABPlan


class IntegrationError(Exception):
    def __init__(self, info: dict):
        self.info = info


class YNABConnector:
    def __init__(self, integration: YNABIntegration):
        self.integration = integration

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

    async def get_plans(self) -> list[YNABPlan]:
        async with self._client() as client:
            res = await client.get("/budgets")
            if res.status_code != 200:
                raise IntegrationError(res.json())

            data = res.json()

        plans = [
            YNABPlan(id=budget["id"], name=budget["name"])
            for budget in data["data"]["budgets"]
        ]

        return plans
