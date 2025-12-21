from uuid import uuid4
from humps import camelize
from python_api.models.plans import Plan
from python_api.models.ynab import YNABPlan
from . import Repository


class TransactionsRepository(Repository):
    def __init__(self, db):
        super().__init__(None, None)
        self.db = db
