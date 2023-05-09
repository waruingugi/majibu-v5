"""Make transaction code column unique

Revision ID: b39b38220ca7
Revises: 7dee92cb908f
Create Date: 2023-05-08 09:38:36.441001

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b39b38220ca7"
down_revision = "7dee92cb908f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, "transactions", ["transaction_id"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "transactions", type_="unique")
    # ### end Alembic commands ###