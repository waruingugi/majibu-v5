from app.db.base_class import Base
from app.accounts.constants import TransactionStatuses
from app.core.helpers import generate_transaction_code
from app.core.config import settings

from sqlalchemy import String, Numeric, text, Text, JSON, Integer, Float, Boolean
from sqlalchemy.orm import mapped_column
from sqlalchemy import DateTime


class Transactions(Base):
    transaction_id = mapped_column(
        String, nullable=False, unique=True, default=generate_transaction_code
    )
    account = mapped_column(String, nullable=False)
    external_transaction_id = mapped_column(String, unique=True, nullable=False)
    initial_balance = mapped_column(Numeric, server_default=text("0.0"), default=0)
    final_balance = mapped_column(Numeric, server_default=text("0.0"), default=0)
    cash_flow = mapped_column(String, nullable=False)
    type = mapped_column(String, nullable=False)
    amount = mapped_column(
        Float(asdecimal=True, decimal_return_scale=settings.MONETARY_DECIMAL_PLACES),
        nullable=True,
    )
    fee = mapped_column(
        Float(asdecimal=True, decimal_return_scale=settings.MONETARY_DECIMAL_PLACES),
        nullable=True,
        server_default=text("0.0"),
        default=0,
    )
    tax = mapped_column(
        Float(asdecimal=True, decimal_return_scale=settings.MONETARY_DECIMAL_PLACES),
        nullable=True,
        server_default=text("0.0"),
        default=0,
    )
    charge = mapped_column(
        Float(asdecimal=True, decimal_return_scale=settings.MONETARY_DECIMAL_PLACES),
        nullable=True,
        server_default=text("0.0"),
        default=0,
    )
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
    Response Section - Success
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


class Withdrawals(Base):
    """
    Records any withdrawals initiated by the user

    Response section.
    Contains attributes populated after posting the request to
    mpesa B2C api url"""

    conversation_id = mapped_column(
        String,
        unique=True,
        comment=(
            "This is a global unique identifier for the transaction request returned by the API "
            "proxy upon successful request submission."
        ),
    )
    originator_conversation_id = mapped_column(
        String,
        comment=(
            "This is a global unique identifier for the transaction request returned by the M-PESA "
            "upon successful request submission."
        ),
    )
    response_code = mapped_column(
        Integer,
        comment=(
            "Indicates the status of the transaction submission. 0 means "
            "successful submission and any other code means an error occurred."
        ),
    )
    response_description = mapped_column(
        Text, comment="This is the description of the request submission status."
    )

    """Response Section - Success
    Contains attributes populated by the callback if payment is successful"""
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
    result_type = mapped_column(
        Integer,
        nullable=True,
        comment=(
            "Indicates whether the transaction was already sent to your listener. Usual value is 0."
        ),
    )

    transaction_id = mapped_column(String, nullable=True)
    transaction_amount = mapped_column(
        Float(asdecimal=True, decimal_return_scale=settings.MONETARY_DECIMAL_PLACES),
        nullable=True,
        comment="This is the Amount that was transacted.",
    )
    working_account_available_funds = mapped_column(
        Float(asdecimal=True, decimal_return_scale=settings.MONETARY_DECIMAL_PLACES),
        nullable=True,
        comment="Available balance of the Working account under the B2C shortcode used in the transaction.",
    )
    utility_account_available_funds = mapped_column(
        Float(asdecimal=True, decimal_return_scale=settings.MONETARY_DECIMAL_PLACES),
        nullable=True,
        comment="Available balance of the Utility account under the B2C shortcode used in the transaction.",
    )
    transaction_date = mapped_column(
        DateTime,
        nullable=True,
        comment=(
            "This is a timestamp that represents the date and time that the "
            "transaction completed."
        ),
    )
    phone_number = mapped_column(
        String,
        nullable=True,
        comment="Phone number of the customer who received the payment.",
    )
    full_name = mapped_column(
        String,
        nullable=True,
        comment="Name of the customer who received the payment.",
    )
    charges_paid_account_available_funds = mapped_column(
        Float(asdecimal=True, decimal_return_scale=settings.MONETARY_DECIMAL_PLACES),
        nullable=True,
        comment="Available balance of the Charges Paid account under the B2C shortcode.",
    )
    is_mpesa_registered_customer = mapped_column(Boolean, nullable=True)
    external_response = mapped_column(JSON, nullable=True)
