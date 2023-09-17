"""Add DuoSession status

Revision ID: 61bee42614be
Revises: e7e28db4a558
Create Date: 2023-09-17 14:52:11.051140

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "61bee42614be"
down_revision = "e7e28db4a558"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("duosession", sa.Column("status", sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("duosession", "status")
    # ### end Alembic commands ###
