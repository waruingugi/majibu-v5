from typing import List
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import templates
from fastapi import FastAPI


def register_exception_handlers(app: FastAPI) -> None:
    template = "templates/info.html"

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        server_errors: List = []

        if hasattr(exc, "detail"):
            server_errors.append(exc.detail)
        elif hasattr(exc, "error_message"):
            server_errors.append(exc.error_message)
        else:
            pass  # No specific error message was found

        return templates.TemplateResponse(
            template,
            {
                "request": request,
                "server_errors": server_errors,
                "title": "New Message",
            },
        )

    @app.exception_handler(429)
    async def custom_429_handler(request, __):
        server_errors: List = ["Too many requests, please try again later"]
        return templates.TemplateResponse(
            template,
            {
                "request": request,
                "server_errors": server_errors,
                "title": "New Message",
            },
        )

    @app.exception_handler(404)
    async def custom_404_handler(request, __):
        server_errors: List = ["The requested page could not be found"]
        return templates.TemplateResponse(
            template,
            {
                "request": request,
                "server_errors": server_errors,
                "title": "New Message",
            },
        )

    @app.exception_handler(401)
    async def custom_401_handler(request, __):
        server_errors: List = []
        return templates.TemplateResponse(
            "auth/templates/login.html",
            {"request": request, "server_errors": server_errors, "title": "Login"},
        )
