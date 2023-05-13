from app.db.base_class import Base
from app.accounts.constants import TransactionStatuses
from app.core.helpers import generate_transaction_code
from app.core.config import settings

from sqlalchemy import String, Numeric, text, Text, JSON, Integer, Float
from sqlalchemy.orm import mapped_column
from sqlalchemy import DateTime


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


class MpesaPayments(Base):
    """
    Records for Payment done through Mpesa.

    Response Section.
    Contains attributes populated by the synchronous response after posting the
    request to mpesa stk push url
    """

    merchant_request_id = mapped_column(
        String, comment="Global unique Identifier for any submitted payment request."
    )
    checkout_request_id = mapped_column(
        String,
        comment="Global unique identifier for the processed transaction request.",
    )
    response_code = mapped_column(
        Integer,
        comment=(
            "Indicates the status of the transaction submission. 0 means "
            "successful submission and any other code means an error occurred."
        ),
    )
    response_description = mapped_column(
        Text, nullable=True, comment="Description message of the Response Code."
    )
    customer_message = mapped_column(
        Text,
        nullable=True,
        comment="Message as an acknowledgement of the payment request submission.",
    )

    """
    Results Section.
    Contains attributes populated by the callback
    """

    result_code = mapped_column(
        Integer,
        nullable=True,
        comment=(
            "Indicates the status of the transaction processing. 0 means "
            "successful processing and any other code means an error occurred."
        ),
    )
    result_description = mapped_column(
        Text, nullable=True, comment="Description message of the Results Code."
    )

    """
    Results Section - Success
    Contains attributes populated by the callback if payment is successful
    """
    amount = mapped_column(
        Float(asdecimal=True, decimal_return_scale=settings.MONETARY_DECIMAL_PLACES),
        nullable=True,
        comment="This is the Amount that was transacted.",
    )
    receipt_number = mapped_column(
        String,
        nullable=True,
        comment="This is the unique M-PESA transaction ID for the payment request.",
    )
    phone_number = mapped_column(
        String,
        nullable=False,
        comment="Phone number of the customer who made the payment.",
    )
    transaction_date = mapped_column(
        DateTime,
        nullable=True,
        comment=(
            "This is a timestamp that represents the date and time that the "
            "transaction completed."
        ),
    )
    external_response = mapped_column(JSON, nullable=True)
