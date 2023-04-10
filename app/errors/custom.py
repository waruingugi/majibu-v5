from enum import Enum


class ErrorCodes(str, Enum):
    NO_CHANGES_DETECTED = "No changes were detected"
    OBJECT_NOT_FOUND = "The specified object does not exist"
