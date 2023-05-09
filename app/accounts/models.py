from app.db.base_class import Base
from app.accounts.constants import TransactionStatuses
from app.accounts.utils import generate_transaction_code

from sqlalchemy import String, Numeric, text, Text, JSON
from sqlalchemy.orm import mapped_column


class Transactions(Base):
    transaction_id = mapped_column(
        String, nullable=False, unique=True, default=generate_transaction_code
    )
    account = mapped_column(String, nullable=False)
    external_transaction_id = mapped_column(String, nullable=False)
    initial_balance = mapped_column(Numeric, server_default=text("0.0"), default=0)
    final_balance = mapped_column(Numeric, server_default=text("0.0"), default=0)
    cash_flow = mapped_column(String, nullable=False)
    type = mapped_column(String, nullable=False)
    fee = mapped_column(Numeric, server_default=text("0.0"), default=0)
    tax = mapped_column(Numeric, server_default=text("0.0"), default=0)
    charge = mapped_column(Numeric, server_default=text("0.0"), default=0)
    status = mapped_column(
        String,
        nullable=False,
        default=TransactionStatuses.PENDING.value,
        server_default=TransactionStatuses.PENDING.value,
    )
    service = mapped_column(String, nullable=False)
    description = mapped_column(Text, nullable=False)
    external_response = mapped_column(JSON, nullable=True)
