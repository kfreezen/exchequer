"""adds currency format

Revision ID: 795862923dd4
Revises: f3625cfdad88
Create Date: 2025-12-20 23:36:34.525248

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "795862923dd4"
down_revision: Union[str, None] = "f3625cfdad88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO currency_formats (currency_code, symbol, symbol_position, decimal_separator, thousand_separator, decimal_places) VALUES
        ('USD', '$', 'before', '.', ',', 2),
        ('EUR', '€', 'after', ',', '.', 2),
        ('GBP', '£', 'before', '.', ',', 2),
        ('JPY', '¥', 'before', '.', ',', 0),
        ('CNY', '¥', 'before', '.', ',', 2);
        """
    )


def downgrade() -> None:
    pass
