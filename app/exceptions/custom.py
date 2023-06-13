from fastapi import HTTPException
from http import HTTPStatus
from app.errors.custom import ErrorCodes


class HttpErrorException(HTTPException):
    def __init__(self, status_code: int, error_code: str, error_message: str) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.error_message = error_message
        self.detail = error_message


class ObjectDoesNotExist(Exception):
    """The specified object was not found"""

    def __init__(self, message: str) -> None:
        self.message = message


class InvalidToken(HttpErrorException):
    def __init__(self) -> None:
        super(InvalidToken, self).__init__(
            status_code=HTTPStatus.UNAUTHORIZED,
            error_code=ErrorCodes.INVALID_TOKEN.name,
            error_message=ErrorCodes.INVALID_TOKEN.value,
        )


class ExpiredAccessToken(HttpErrorException):
    def __init__(self) -> None:
        super(ExpiredAccessToken, self).__init__(
            status_code=HTTPStatus.UNAUTHORIZED,
            error_code=ErrorCodes.EXPIRED_AUTHORIZATION_TOKEN.name,
            error_message=ErrorCodes.EXPIRED_AUTHORIZATION_TOKEN.value,
        )


class IncorrectCredentials(HttpErrorException):
    def __init__(self) -> None:
        super(IncorrectCredentials, self).__init__(
            status_code=HTTPStatus.UNAUTHORIZED,
            error_code=ErrorCodes.INCORRECT_USERNAME_OR_PASSWORD.name,
            error_message=ErrorCodes.INCORRECT_USERNAME_OR_PASSWORD.value,
        )


class InactiveAccount(HttpErrorException):
    def __init__(self) -> None:
        super(InactiveAccount, self).__init__(
            status_code=HTTPStatus.UNAUTHORIZED,
            error_code=ErrorCodes.INACTIVE_ACCOUNT.name,
            error_message=ErrorCodes.INACTIVE_ACCOUNT.value,
        )


class InsufficientUserPrivileges(HttpErrorException):
    def __init__(self) -> None:
        super(InsufficientUserPrivileges, self).__init__(
            status_code=HTTPStatus.BAD_REQUEST,
            error_code=ErrorCodes.USERS_PRIVILEGES_NOT_ENOUGH.name,
            error_message=ErrorCodes.USERS_PRIVILEGES_NOT_ENOUGH.value,
        )


class STKPushFailed(HttpErrorException):
    def __init__(self) -> None:
        super(STKPushFailed, self).__init__(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code=ErrorCodes.STK_PUSH_FAILED.name,
            error_message=ErrorCodes.STK_PUSH_FAILED.value,
        )


class B2CPaymentFailed(Exception):
    def __init__(self, message: str = ErrorCodes.B2C_PAYMENT_FAILED.value) -> None:
        self.message = message


class SimilarWithdrawalRequest(Exception):
    """The user initiated a withdrawal request while a previous one
    is still being processed."""

    def __init__(self) -> None:
        self.message = ErrorCodes.SIMILAR_WITHDRAWAL_REQUEST.value


class InvalidEnumValue(Exception):
    """An invalid enum value was provided"""

    def __init__(self, message: str = "An invalid enum value was provided") -> None:
        self.message = message


class QuestionExistsInASession(Exception):
    """Question exists in another session"""

    def __init__(self, message: str) -> None:
        self.message = message


class FewQuestionsInSession(Exception):
    """Session has invalid number of questions"""

    def __init__(self) -> None:
        self.message = ErrorCodes.SESSION_HAS_INVALID_NO_OF_QUESTIONS.value
