from python_api.models import CamelModel


class YNABPlan(CamelModel):
    id: str
    name: str
    currency_code: str | None = None
