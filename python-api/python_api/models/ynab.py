from python_api.models import CamelModel


class ImportModel(CamelModel):
    imported_document: dict
    import_revision: int | None
    import_source: str
    import_id: str


class PlanImport(ImportModel):
    name: str
    currency_code: str | None = None


class PayeeImport(ImportModel):
    name: str
    transfer_account_id: str | None = None


class EnvelopeImport(ImportModel):
    name: str
    hidden: bool


class AccountImport(ImportModel):
    name: str
    type: str
    closed: bool


class TransactionImport(ImportModel):
    id: str
    date: str
    amount: int
    account_id: str
    payee_id: str | None = None
    category_id: str | None = None
    transfer_account_id: str | None = None
    transfer_transaction_id: str | None = None
    matched_transaction_id: str | None = None
    parent_transaction_id: str | None = None
    description: str | None = None
    cleared: str
    approved: bool
