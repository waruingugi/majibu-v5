"""Add amount field to Transactions model

Revision ID: 3b449cf5558f
Revises: e4607196b3a7
Create Date: 2023-05-13 16:07:58.135389

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3b449cf5558f"
down_revision = "e4607196b3a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "transactions",
        sa.Column(
            "amount", sa.Float(asdecimal=True, decimal_return_scale=2), nullable=True
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("transactions", "amount")
    # ### end Alembic commands ###