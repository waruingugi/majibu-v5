from enum import Enum


class ErrorCodes(str, Enum):
    INVALID_PHONENUMBER = "The phone number {} is not valid"
    INVALID_OTP = "The OTP entered is not correct. Please try again"
    OBJECT_NOT_FOUND = "The specified object does not exist"
    NO_CHANGES_DETECTED = "No changes were detected"
    INACTIVE_ACCOUNT = "This account is currently inactive"
