"""Update phone number field to phone field in MpesaPayments model

Revision ID: fa9620b8ca0f
Revises: 6776e0bea20c
Create Date: 2023-05-12 17:03:48.329870

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fa9620b8ca0f"
down_revision = "6776e0bea20c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("mpesapayments", sa.Column("phone", sa.String(), nullable=False))
    op.drop_column("mpesapayments", "phone_number")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "mpesapayments",
        sa.Column("phone_number", sa.VARCHAR(), autoincrement=False, nullable=False),
    )
    op.drop_column("mpesapayments", "phone")
    # ### end Alembic commands ###
