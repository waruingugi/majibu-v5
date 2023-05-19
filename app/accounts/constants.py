from enum import Enum


# SMS message sent to user on M-Pesa deposit
MPESA_PAYMENT_DEPOSIT = (
    "You've successfully deposited Ksh{} for your account {}. "
    "New balance is Ksh{}. "
    "Thank your for choosing Majibu!"
)

# M-Pesa STKPush deposit description
STKPUSH_DEPOSIT_DESCRPTION = "Deposit of Ksh {} " "for account {} using M-Pesa STKPush."

# M-Pesa direct paybill payment description
PAYBILL_DEPOSIT_DESCRIPTION = (
    "Deposit of Ksh {} " "for account {} using M-Pesa paybill."
)


class B2CMpesaCommandIDs(str, Enum):
    SALARYPAYMENT = "SalaryPayment"
    BUSINESSPAYMENT = "BusinessPayment"
    PROMOTIONPAYMENT = "PromotionPayment"


class TransactionStatuses(str, Enum):
    PENDING = "PENDING"
    SUCCESSFUL = "SUCCESSFUL"
    REFUNDED = "REFUNDED"


class MpesaAccountTypes(str, Enum):
    PAYBILL = "CustomerPayBillOnline"
    BUYGOODS = "CustomerBuyGoodsOnline"


class TransactionCashFlow(str, Enum):
    INWARD = "INWARD"
    OUTWARD = "OUTWARD"


class TransactionTypes(str, Enum):
    REWARD = "REWARD"
    PAYMENT = "PAYMENT"
    BONUS = "BONUS"


class TransactionServices(str, Enum):
    MAJIBU = "MAJIBU"
    MPESA = "MPESA"


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
