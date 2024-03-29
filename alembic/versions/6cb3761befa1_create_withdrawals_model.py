"""Create Withdrawals model

Revision ID: 6cb3761befa1
Revises: 3b449cf5558f
Create Date: 2023-05-17 14:05:13.418044

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6cb3761befa1"
down_revision = "3b449cf5558f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "withdrawals",
        sa.Column(
            "conversation_id",
            sa.String(),
            nullable=True,
            comment="This is a global unique identifier for the transaction request returned by the API proxy upon successful request submission.",
        ),
        sa.Column(
            "originator_conversation_id",
            sa.String(),
            nullable=True,
            comment="This is a global unique identifier for the transaction request returned by the M-PESA upon successful request submission.",
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
            comment="This is the description of the request submission status.",
        ),
        sa.Column(
            "result_code",
            sa.Integer(),
            nullable=True,
            comment="Indicates the status of the transaction processing. 0 means successful processing and any other code means an error occurred.",
        ),
        sa.Column(
            "result_description",
            sa.Text(),
            nullable=True,
            comment="Description message of the Results Code.",
        ),
        sa.Column(
            "result_type",
            sa.Integer(),
            nullable=True,
            comment="Indicates whether the transaction was already sent to your listener. Usual value is 0.",
        ),
        sa.Column("transaction_id", sa.String(), nullable=True),
        sa.Column(
            "transaction_amount",
            sa.Float(asdecimal=True, decimal_return_scale=2),
            nullable=True,
            comment="This is the Amount that was transacted.",
        ),
        sa.Column(
            "working_account_available_funds",
            sa.Float(asdecimal=True, decimal_return_scale=2),
            nullable=True,
            comment="Available balance of the Working account under the B2C shortcode used in the transaction.",
        ),
        sa.Column(
            "utility_account_available_funds",
            sa.Float(asdecimal=True, decimal_return_scale=2),
            nullable=True,
            comment="Available balance of the Utility account under the B2C shortcode used in the transaction.",
        ),
        sa.Column(
            "transaction_date",
            sa.DateTime(),
            nullable=True,
            comment="This is a timestamp that represents the date and time that the transaction completed.",
        ),
        sa.Column(
            "phone_number",
            sa.String(),
            nullable=True,
            comment="Phone number of the customer who received the payment.",
        ),
        sa.Column(
            "full_name",
            sa.String(),
            nullable=True,
            comment="Name of the customer who received the payment.",
        ),
        sa.Column(
            "charges_paid_account_available_funds",
            sa.Float(asdecimal=True, decimal_return_scale=2),
            nullable=True,
            comment="Available balance of the Charges Paid account under the B2C shortcode.",
        ),
        sa.Column("is_mpesa_registered_customer", sa.Boolean(), nullable=True),
        sa.Column("external_response", sa.JSON(), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("withdrawals")
    # ### end Alembic commands ###
