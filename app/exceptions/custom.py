from fastapi import HTTPException
from http import HTTPStatus
from app.errors.custom import ErrorCodes


class HttpErrorException(HTTPException):
    def __init__(self, status_code: int, error_code: str, error_message: str) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.error_message = error_message
        self.detail = error_message


class ObjectDoesNotExist(HttpErrorException):
    """The specified object was not found"""

    def __init__(self) -> None:
        super(ObjectDoesNotExist, self).__init__(
            status_code=HTTPStatus.NOT_FOUND,
            error_code=ErrorCodes.OBJECT_NOT_FOUND.name,
            error_message=ErrorCodes.OBJECT_NOT_FOUND.value,
        )
