"""Add Row-level security

Revision ID: aeccfcff3ff1
Revises: b5a0a4bad179
Create Date: 2025-11-28 19:38:28.750035

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "aeccfcff3ff1"
down_revision: Union[str, None] = "b5a0a4bad179"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tables = [
        "accounts",
        "entities",
        "envelopes",
        "transactions",
    ]

    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

        op.execute(
            f"""
            CREATE POLICY rls_policy ON {table}
            FOR ALL
            USING (user_id = current_setting('app.current_user_id')::uuid);
            """
        )
    pass


def downgrade() -> None:
    tables = [
        "accounts",
        "entities",
        "envelopes",
        "transactions",
    ]

    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS rls_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
