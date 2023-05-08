from enum import Enum


class ErrorCodes(str, Enum):
    INVALID_PHONENUMBER = "The phone number {} is not valid"
    INVALID_OTP = "The code you entered is not correct. Please try again"
    OBJECT_NOT_FOUND = "The specified object does not exist"
    NO_CHANGES_DETECTED = "No changes were detected"
    INACTIVE_ACCOUNT = "This account is currently inactive. Please contact support"
    INVALID_TOKEN = "Could not validate your token"
    EXPIRED_AUTHORIZATION_TOKEN = "The authorization token expired"
    INCORRECT_USERNAME_OR_PASSWORD = "Incorrect username or password"
    USERS_PRIVILEGES_NOT_ENOUGH = "This user doesn't have enough privileges"
    STKPushFailed = (
        "An error ocurred while initiating the STKPush request"
        "Please try the payment again using our Business PayBill"
    )
