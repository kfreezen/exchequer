"""Contains the TransactionsRepository class for managing transactions in a database.

This class should be used to insert and fetch transactions and transaction reports.
"""

import uuid

from datetime import datetime
from python_api.repositories import Repository

AMORTIZATION_SCHEDULE = {
    "monthly": None,
    "two_month": {"months": 2},
    "three_month": {"months": 3},
    "six_month": {"months": 6},
    "yearly": {"months": 12},
}


def add_months(date: int, month: int):
    dt = datetime.fromtimestamp(date)
    nmonth = dt.month + month
    nyear = dt.year
    day = dt.day

    if nmonth > 12:
        nyear = dt.year + 1
        nmonth -= 12

    if day > 30 and nmonth in [4, 6, 9, 11]:
        day = 30
    elif day > 28 and nmonth == 2:
        day = 28

    return int(dt.replace(year=nyear, month=nmonth, day=day).timestamp())


class TransactionsRepository(Repository):
    def __init__(self, db):
        super().__init__(None, None)

        self.db = db

    async def insert_transaction_no_duplicate(
        self,
        user_id,
        source,
        transaction_id,
        product_id,
        price,
        tax_percentage,
        commission_percentage,
        takehome_amount,
        created_at,
        applied_at: int,
        currency: str | None = None,
    ):
        """Inserts a transaction into the database if it does not already exist.

        Args:
            user_id (str): The ID of the user associated with the transaction.
            source (str): The source of the transaction (e.g., "stripe", "paypal").
            transaction_id (str): The unique identifier for the transaction.
            product_id (str): The ID of the product associated with the transaction.
            price (float): The total price of the transaction.
            tax_percentage (float): The percentage of tax applied to the transaction.
            commission_percentage (float): The percentage of commission applied to the transaction.
            takehome_amount (float): The amount that remains after deductions.
            created_at (int): The timestamp when the transaction was created.
            applied_at (int): The timestamp when the transaction was applied.
            currency (str | None, optional): The currency of the transaction. Defaults to None.

        Notes:
            There is no business case for duration to be included in this method currently.
        """

        main_id = uuid.uuid4()
        async with self.db.cursor() as cur:
            await cur.execute(
                "SELECT * FROM transactions WHERE transaction_id = %s",
                (transaction_id,),
            )
            if await cur.fetchone():
                return
            await cur.execute(
                self.INSERT_TRANSACTION_QUERY,
                {
                    "id": main_id,
                    "user_id": user_id,
                    "source": source,
                    "transaction_id": transaction_id,
                    "product_id": product_id,
                    "price": price,
                    "tax_percentage": tax_percentage,
                    "commission_percentage": commission_percentage,
                    "takehome_amount": takehome_amount,
                    "created_at": created_at,
                    "applied_at": applied_at,
                    "currency": currency,
                    "amortized_transaction_id": None,
                },
            )

    async def delete_amortizations(self, transaction_id):
        async with self.db.cursor() as cur:
            await cur.execute(
                "SELECT id FROM transactions WHERE transaction_id = %s",
                (transaction_id,),
            )

            id_row = await cur.fetchone()

            await cur.execute(
                "DELETE FROM transactions WHERE amortized_transaction_id = %s",
                (id_row["id"],),
            )

            await cur.execute(
                "UPDATE transactions SET applied_at = created_at WHERE id = %s",
                (id_row["id"],),
            )

    async def get_transaction(self, store, store_transaction_id):
        async with self.db.cursor() as cur:
            await cur.execute(
                "SELECT * FROM transactions WHERE source = %s AND transaction_id = %s",
                (store, store_transaction_id),
            )
            return await cur.fetchone()

    async def insert_transaction(
        self,
        user_id,
        source,
        transaction_id,
        product_id,
        price,
        tax_percentage,
        commission_percentage,
        takehome_percentage,
        takehome_amount,
        created_at,
        applied_at: int,
        duration,
        currency: str | None = None,
    ):
        main_id = uuid.uuid4()

        amortization = AMORTIZATION_SCHEDULE.get(duration, None)
        transactions = [
            {
                "id": main_id,
                "user_id": user_id,
                "source": source,
                "transaction_id": transaction_id,
                "product_id": product_id,
                "price": price,
                "tax_percentage": tax_percentage,
                "commission_percentage": commission_percentage,
                "takehome_percentage": takehome_percentage,
                "takehome_amount": takehome_amount,
                "created_at": created_at,
                "transacted_at": created_at,
                "applied_at": applied_at,
                "currency": currency,
                "amortized_transaction_id": None,
            }
        ]

        if amortization:
            transactions[0]["applied_at"] = None

            next_applied_at = applied_at
            months = amortization["months"]

            for i in range(0, amortization["months"]):
                assert main_id is not None

                next_applied_at = add_months(applied_at, i)
                transactions.append(
                    {
                        "id": uuid.uuid4(),
                        "user_id": user_id,
                        "source": f"{source}.amortized",
                        "transaction_id": f"{transaction_id}.{i}",
                        "product_id": product_id,
                        "price": price / months,
                        "tax_percentage": tax_percentage,
                        "commission_percentage": commission_percentage,
                        "takehome_percentage": takehome_percentage,
                        "takehome_amount": takehome_amount / months,
                        "created_at": created_at,
                        "transacted_at": created_at,
                        "applied_at": next_applied_at,
                        "currency": currency,
                        "amortized_transaction_id": main_id,
                    }
                )

        failed = False
        async with self.db.cursor() as cur:
            inserted = 0
            try:
                await cur.executemany(
                    self.INSERT_TRANSACTION_QUERY,
                    transactions,
                )
                inserted += cur.rowcount

            except Exception as e:
                for transaction in transactions:
                    transaction["user_id"] = None
                await self.db.rollback()
                print(e)
                inserted = 0
                failed = True

        if failed:
            async with self.db.cursor() as cur:
                for transaction in transactions:
                    await cur.execute(
                        self.INSERT_TRANSACTION_QUERY,
                        transaction,
                    )

                    inserted += cur.rowcount
        return inserted, len(transactions)

    INSERT_TRANSACTION_QUERY = """
        INSERT INTO transactions (
            id,
            user_id,
            source,
            transaction_id,
            product_id,
            price,
            tax_percentage,
            commission_percentage,
            takehome_percentage,
            takehome_amount,
            created_at,
            transacted_at,
            applied_at,
            currency,
            amortized_transaction_id
        )
        VALUES
        (
        %(id)s,
        %(user_id)s,
        %(source)s,
        %(transaction_id)s,
        %(product_id)s,
        %(price)s,
        %(tax_percentage)s,
        %(commission_percentage)s,
        %(takehome_percentage)s,
        %(takehome_amount)s,
        %(created_at)s,
        %(transacted_at)s,
        %(applied_at)s,
        %(currency)s,
        %(amortized_transaction_id)s
        )
        ON CONFLICT DO NOTHING
    """
