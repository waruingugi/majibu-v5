from enum import Enum
from app.core.config import settings


# SMS message sent to user on M-Pesa deposit
MPESA_PAYMENT_DEPOSIT = (
    "You've successfully deposited Ksh{} for your account {}. "
    "New balance is Ksh{}. "
    "Thank your for choosing Majibu!"
)

# M-Pesa STKPush deposit description
STKPUSH_DEPOSIT_DESCRPTION = "Deposit of Ksh {} for account {} using M-Pesa STKPush."

# M-Pesa direct paybill payment description
PAYBILL_DEPOSIT_DESCRIPTION = "Deposit of Ksh {} for account {} using M-Pesa paybill."

# M-Pesa B2C payment description
PAYBILL_B2C_DESCRIPTION = "Payment of Ksh {} for account {} using B2C payment."

# Withdrawal to play session description
SESSION_WITHDRAWAL_DESCRIPTION = "Withdrawal by user: {} for session id: {}."

# Deposit from winning a session description
SESSION_WIN_DESCRIPION = "Deposit to user: {} for winning session id: {}"

# Refund for party_a for playing a session description
REFUND_SESSION_DESCRIPTION = "Refund user: {} for playing session id: {}"

# Partially refund for party_a for playing a session description
PARTIALLY_REFUND_SESSION_DESCRIPTION = (
    "Partially refund user: {} for playing session id: {}"
)

# SMS message sent to user on winning a session
SESSION_WIN_MESSAGE = (
    "Congrats! You've won KES {} for your {} session. "
    "Your skill paid off big time. Good luck on your next session!"
)

# SMS message sent to user on losing a session
SESSION_LOSS_MESSAGE = (
    "You lost {} session to your opponent. "
    "Please check Majibu history for full results."
)

# SMS message sent to user on refund
SESSION_REFUND_MESSAGE = (
    f"You've received a {int(settings.SESSION_REFUND_RATIO * 100)}% refund of "
    "KES {} for your {} session. "
    "Thank you for choosing Majibu and best of luck on your next session! "
    "Click here to join Majibu whatsapp group: https://bit.ly/mjbu"
)

# SMS message sent to user on partial refund
SESSION_PARTIAL_REFUND_MESSAGE = (
    f"You've received a {int(settings.SESSION_PARTIAL_REFUND_RATIO * 100)}% partial refund of "
    "KES {} for your {} session. "
    "Please attempt atleast one question to be paired or to receive a full refund on Majibu"
)

# SMS message sent to user on M-Pesa withdrawal
MPESA_PAYMENT_WITHDRAW = (
    "You've successfully withdrawn Ksh{} for your account {}. "
    f"Transaction cost Ksh{settings.MPESA_B2C_CHARGE}. "
    "New balance is Ksh{}. "
    "Click here to join Majibu whatsapp group: https://bit.ly/mjbu"
)

# SMS message to user on wallet deduction to play a session
WALLET_DEDUCTION_FOR_SESSION = (
    "{} Confirmed. "
    f"Withdraw Ksh{settings.SESSION_AMOUNT} from account "
    "{} for Majibu session. "
    "New balance is Ksh{}. "
    "Click here to join Majibu whatsapp group: https://bit.ly/mjbu"
)


class B2CMpesaCommandIDs(str, Enum):
    SALARYPAYMENT = "SalaryPayment"
    BUSINESSPAYMENT = "BusinessPayment"
    PROMOTIONPAYMENT = "PromotionPayment"


class TransactionStatuses(str, Enum):
    PENDING = "PENDING"
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"


class MpesaAccountTypes(str, Enum):
    PAYBILL = "CustomerPayBillOnline"
    BUYGOODS = "CustomerBuyGoodsOnline"


class TransactionCashFlow(str, Enum):
    INWARD = "INWARD"
    OUTWARD = "OUTWARD"


class TransactionTypes(str, Enum):
    BONUS = "BONUS"
    REFUND = "REFUND"
    REWARD = "REWARD"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class TransactionServices(str, Enum):
    MPESA = "MPESA"
    MAJIBU = "MAJIBU"
    SESSION = "SESSION"


MPESA_WHITE_LISTED_IPS = [
    "196.201.214.200",
    "196.201.214.206",
    "196.201.213.114",
    "196.201.214.207",
    "196.201.214.208",
    "196.201.213.44",
    "196.201.212.127",
    "196.201.212.138",
    "196.201.212.129",
    "196.201.212.136",
    "196.201.212.74",
    "196.201.212.69",
]
