from enum import Enum


class ErrorCodes(str, Enum):
    B2C_PAYMENT_FAILED = "An error ocurred while initiating a B2C payment."
    EXPIRED_AUTHORIZATION_TOKEN = "The authorization token expired"
    INACTIVE_ACCOUNT = "This account is currently inactive. Please contact support"
    INVALID_TOKEN = "Could not validate your token"
    INVALID_PHONENUMBER = "The phone number {} is not valid"
    INVALID_OTP = "The code you entered is not correct. Please try again"
    INSUFFICIENT_BALANCE = "You have insufficient balance. Please top up and try again"
    INCORRECT_USERNAME_OR_PASSWORD = "Incorrect username or password"
    MAINTENANCE_MODE = "The business is currently under going maintenance."
    NO_AVAILABLE_SESSION = (
        "There are no available sessions at the moment. Please try again later"
    )
    NO_CHANGES_DETECTED = "No changes were detected"
    OBJECT_NOT_FOUND = "The specified object does not exist"
    STK_PUSH_FAILED = (
        "An error ocurred while initiating the STKPush request. "
        "Please try the payment again using our Business PayBill"
    )
    SIMILAR_WITHDRAWAL_REQUEST = (
        "A previous withdrawal request is being processed. " "Please try again later."
    )
    SESSION_HAS_INVALID_NO_OF_QUESTIONS = (
        "Session has invalid questions number of questions"
    )
    SESSION_IN_QUEUE = (
        "Your previous session is still being processed. "
        "Please try again once you're paired or refunded"
    )
    SESSION_EXPIRED = (
        "You can not request a session past it's expiry time. "
        "Please review session rules for more information."
    )
    USERS_PRIVILEGES_NOT_ENOUGH = "This user doesn't have enough privileges"
