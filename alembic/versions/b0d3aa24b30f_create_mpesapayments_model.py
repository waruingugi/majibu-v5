"""Create MpesaPayments model

Revision ID: b0d3aa24b30f
Revises: b39b38220ca7
Create Date: 2023-05-12 11:09:21.625577

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b0d3aa24b30f"
down_revision = "b39b38220ca7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "mpesapayments",
        sa.Column("account", sa.String(), nullable=False),
        sa.Column(
            "merchant_request_id",
            sa.String(),
            nullable=True,
            comment="Global unique Identifier for any submitted payment request.",
        ),
        sa.Column(
            "checkout_request_id",
            sa.String(),
            nullable=True,
            comment="Global unique identifier for the processed transaction request.",
        ),
        sa.Column(
            "response_code",
            sa.Integer(),
            nullable=True,
            comment="Indicates the status of the transaction submission. 0 means successful submission and any other code means an error occurred.",
        ),
        sa.Column(
            "response_description",
            sa.Text(),
            nullable=True,
            comment="Description message of the Response Code.",
        ),
        sa.Column(
            "customer_message",
            sa.Text(),
            nullable=True,
            comment="Message as an acknowledgement of the payment request submission.",
        ),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("mpesapayments")
    # ### end Alembic commands ###
