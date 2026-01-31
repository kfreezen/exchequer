from decimal import Decimal
import json
from uuid import uuid4
from humps import camelize

from python_api.models.transactions import Transaction
from python_api.models.ynab import TransactionImport
from . import Repository


class TransactionsRepository(Repository):
    def __init__(self, db):
        super().__init__(None, None)
        self.db = db

    async def finalize_transaction_imports(self, user_id: str, import_source: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                UPDATE transactions AS t
                SET
                    transfer_transaction_id = t2.id
                FROM transactions AS t2
                WHERE
                    t.user_id = %(user_id)s AND
                    t2.user_id = %(user_id)s AND
                    t.imported_document->>'transfer_transaction_id' IS NOT NULL AND
                    t.imported_document->>'transfer_transaction_id' = t2.import_id
                """,
                {
                    "user_id": user_id,
                    "import_source": import_source,
                },
            )

            await cur.execute(
                """
                UPDATE transactions AS t
                SET
                    matched_transaction_id = t2.id
                FROM transactions AS t2
                WHERE
                    t.user_id = %(user_id)s AND
                    t2.user_id = %(user_id)s AND
                    t.imported_document->>'matched_transaction_id' IS NOT NULL AND
                    t.imported_document->>'matched_transaction_id' = t2.import_id
                """,
                {
                    "user_id": user_id,
                    "import_source": import_source,
                },
            )

            await cur.execute(
                """
                UPDATE transactions AS t
                SET
                    parent_transaction_id = t2.id
                FROM transactions AS t2
                WHERE
                    t.user_id = %(user_id)s AND
                    t2.user_id = %(user_id)s AND
                    t.imported_document->>'transaction_id' IS NOT NULL AND
                    t.imported_document->>'transaction_id' = t2.import_id
                """,
                {
                    "user_id": user_id,
                    "import_source": import_source,
                },
            )

    async def import_transaction(self, user_id: str, transaction: TransactionImport):
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO transactions (
                    id, 
                    import_id,
                    user_id,
                    account_id,
                    amount,
                    date,
                    description,
                    cleared, 
                    approved,
                    payee_id,
                    envelope_id,
                    transfer_account_id,
                    created_at,
                    updated_at,
                    imported_document,
                    import_revision,
                    import_source)
                SELECT
                    %(id)s,
                    %(import_id)s,
                    %(user_id)s,
                    (SELECT a.id FROM accounts a WHERE a.import_id = %(account_id)s),
                    %(amount)s,
                    %(date)s,
                    %(memo)s,
                    %(cleared)s,
                    %(approved)s,
                    (SELECT p.id FROM payees p WHERE p.import_id = %(payee_id)s),
                    (SELECT e.id FROM envelopes e WHERE e.import_id = %(envelope_id)s),
                    (SELECT a.id FROM accounts a WHERE a.import_id = %(transfer_account_id)s),
                    NOW(),
                    NOW(),
                    %(imported_document)s,
                    %(import_revision)s,
                    %(import_source)s
                ON CONFLICT (import_id) DO UPDATE SET
                    amount = EXCLUDED.amount,
                    date = EXCLUDED.date,
                    account_id = EXCLUDED.account_id,
                    payee_id = EXCLUDED.payee_id,
                    envelope_id = EXCLUDED.envelope_id,
                    transfer_account_id = EXCLUDED.transfer_account_id,
                    description = EXCLUDED.description,
                    cleared = EXCLUDED.cleared,
                    updated_at = NOW(),
                    imported_document = EXCLUDED.imported_document,
                    import_revision = EXCLUDED.import_revision,
                    import_source = EXCLUDED.import_source,
                    approved = EXCLUDED.approved
                RETURNING id, user_id, amount, date, payee_id, envelope_id, created_at, updated_at
                """,
                {
                    "id": uuid4(),
                    "import_id": transaction.import_id,
                    "user_id": user_id,
                    "account_id": transaction.account_id,
                    "amount": Decimal(transaction.amount) / Decimal(1000),
                    "date": transaction.date,
                    "memo": transaction.description,
                    "cleared": transaction.cleared,
                    "import_source": transaction.import_source,
                    "transfer_account_id": transaction.transfer_account_id,
                    "payee_id": transaction.payee_id,
                    "envelope_id": transaction.category_id,
                    "imported_document": json.dumps(transaction.imported_document),
                    "import_revision": transaction.import_revision,
                    "approved": transaction.approved,
                },
            )

            row = await cur.fetchone()
            if not row or not row["id"]:
                return await self.get_transaction_by_import_id(transaction.import_id)

            return camelize(row)  # Assuming a Transaction model exists

    FIELDS = [
        "id",
        "user_id",
        "amount",
        "description",
        "date",
        "payee_id",
        "entity_id",
        "envelope_id",
        "created_at",
        "updated_at",
        "import_id",
        "transfer_transaction_id",
        "matched_transaction_id",
        "parent_transaction_id",
    ]
    FIELD_STRING = ", ".join([f"t.{f}" for f in FIELDS])

    async def get_transaction_by_import_id(self, import_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {self.FIELD_STRING}
                FROM transactions t
                WHERE import_id = %(import_id)s
                """,
                {"import_id": import_id},
            )

            row = await cur.fetchone()
            if row:
                return camelize(row)  # Assuming a Transaction model exists

            return None

    async def get_transaction_by_id(self, transaction_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {self.FIELD_STRING}
                FROM transactions t
                WHERE id = %(transaction_id)s
                """,
                {"transaction_id": transaction_id},
            )

            row = await cur.fetchone()
            if row:
                return camelize(row)  # Assuming a Transaction model exists
            return None

    async def get_user_transactions(self, user_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {self.FIELD_STRING}
                FROM transactions t
                WHERE user_id = %(user_id)s
                """,
                {"user_id": user_id},
            )

            rows = await cur.fetchall()
            return [
                camelize(row) for row in rows
            ]  # Assuming a Transaction model exists

    async def get_last_import_revision(
        self, user_id: str, import_source: str
    ) -> int | None:
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                SELECT MAX(import_revision) AS last_import_revision
                FROM transactions t
                WHERE user_id = %(user_id)s AND import_source = %(import_source)s
                """,
                {
                    "user_id": user_id,
                    "import_source": import_source,
                },
            )

            row = await cur.fetchone()
            if row and row["last_import_revision"] is not None:
                return row["last_import_revision"]
            return None

    async def get_transactions_by_envelope_id(self, user_id: str, envelope_id: str):
        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {self.FIELD_STRING},
                    p.name AS payee_name
                FROM transactions t
                LEFT JOIN payees p ON t.payee_id = p.id
                WHERE t.user_id = %(user_id)s AND t.envelope_id = %(envelope_id)s
                """,
                {"user_id": user_id, "envelope_id": envelope_id},
            )

            rows = await cur.fetchall()
            return [
                Transaction.model_validate(camelize(row)) for row in rows
            ]  # Assuming a Transaction model exists

    async def assign_transactions_to_entity(
        self, user_id: str, entity_id: str, transaction_ids: list[str]
    ):
        async with self.db.cursor() as cur:
            await cur.execute(
                f"""
                UPDATE transactions
                SET entity_id = %(entity_id)s
                WHERE user_id = %(user_id)s AND id = ANY(%(transaction_ids)s)
                """,
                {
                    "user_id": user_id,
                    "entity_id": entity_id,
                    "transaction_ids": transaction_ids,
                },
            )

            return
