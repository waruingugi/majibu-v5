from enum import Enum


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


class TransactionType(str, Enum):
    REWARD = "REWARD"
    PAYMENT = "PAYMENT"
    BONUS = "BONUS"


class TransactionStatus(str, Enum):
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
