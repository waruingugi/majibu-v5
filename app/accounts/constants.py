from enum import Enum


class TransactionStatuses(Enum):
    PENDING = "PENDING"
    SUCCESSFUL = "SUCCESSFUL"
    REFUNDED = "REFUNDED"
