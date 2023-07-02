from enum import Enum


class ErrorCodes(str, Enum):
    INVALID_PHONENUMBER = "The phone number {} is not valid"
    INVALID_OTP = "The code you entered is not correct. Please try again"
    INSUFFICIENT_BALANCE = "You have insufficient balance. Please top up and try again"
    OBJECT_NOT_FOUND = "The specified object does not exist"
    NO_CHANGES_DETECTED = "No changes were detected"
    INACTIVE_ACCOUNT = "This account is currently inactive. Please contact support"
    INVALID_TOKEN = "Could not validate your token"
    EXPIRED_AUTHORIZATION_TOKEN = "The authorization token expired"
    INCORRECT_USERNAME_OR_PASSWORD = "Incorrect username or password"
    USERS_PRIVILEGES_NOT_ENOUGH = "This user doesn't have enough privileges"
    STK_PUSH_FAILED = (
        "An error ocurred while initiating the STKPush request. "
        "Please try the payment again using our Business PayBill"
    )
    SIMILAR_WITHDRAWAL_REQUEST = (
        "A previous withdrawal request is being processed. " "Please try again later."
    )
    B2C_PAYMENT_FAILED = "An error ocurred while initiating a B2C payment."
    SESSION_HAS_INVALID_NO_OF_QUESTIONS = (
        "Session has invalid questions number of questions"
    )
    MAINTENANCE_MODE = "The business is currently under going maintenance."
    SESSION_IN_QUEUE = (
        "Your previous session is still being processed. "
        "Please try again once you're paired or refunded"
    )
    NO_AVAILABLE_SESSION = (
        "There are no available sessions at the moment. Please try again later"
    )
