from typing import Callable

from fastapi.routing import APIRoute
from fastapi import Request, Response
from fastapi import BackgroundTasks

from app.core.raw_logger import logger


RESTRICTED_PAYLOAD_URLS = [
    "auth//validate-otp/",
]


class LoggingRoute(APIRoute):
    """Log every request and response from the API"""

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request_log_data = await prepare_request_logging_data(request)
            response: Response = await original_route_handler(request)

            if not response.background:
                response.background = BackgroundTasks()

            response_log_data = dict(
                status_code=response.status_code,
                response_id=request.headers.get("x-request-id", None),
                user_id=request._headers.get("x-user-id", None),
            )

            request_identifier = f"by {response_log_data['user_id']}"

            # Pop cookie from logs because it contains access token
            headers: dict = request_log_data.pop("headers", {})
            headers.pop("cookie", None)
            request_log_data["headers"] = headers

            # Identify request by user_id or request_id/response_id
            request_identifier = (
                f"User {response_log_data['user_id']}"
                if response_log_data["user_id"]
                else f"ID {response_log_data['response_id']}"
            )

            response.background.add_task(  # type: ignore [attr-defined]
                logger.info, f"Request {request_identifier}: {request_log_data}"
            )
            response.background.add_task(  # type: ignore [attr-defined]
                logger.info, f"Response {request_identifier}: {response_log_data}"
            )

            return response

        return custom_route_handler


def should_log_payload(request: Request) -> bool:
    """Do not log requests in RESTRICTED_PAYLOAD_URLS"""
    return not (request.url.path in RESTRICTED_PAYLOAD_URLS)


async def prepare_request_logging_data(
    request: Request, read_body: bool = True
) -> dict:
    """Format request to dictionary"""
    payload = None
    if read_body and should_log_payload(request):
        payload = await request.body()

    headers_for_logging = dict(request.headers)
    headers_for_logging.pop("authorization", None)

    request_log_data = dict(
        method=request.method,
        url=str(request.url),
        headers=headers_for_logging,
        payload=payload,
    )
    return request_log_data
