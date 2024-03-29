"""Create questions model

Revision ID: eeec27641f8b
Revises: 32799b7e6868
Create Date: 2023-05-01 20:07:08.633041

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "eeec27641f8b"
down_revision = "32799b7e6868"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "questions",
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("questions")
    # ### end Alembic commands ###
