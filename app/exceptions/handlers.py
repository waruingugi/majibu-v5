from typing import List
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import templates
from fastapi import FastAPI


def register_exception_handlers(app: FastAPI) -> None:
    template = "templates/info.html"

    def format_exception(exc) -> List:
        server_errors: List = []

        if hasattr(exc, "detail"):
            server_errors.append(exc.detail)
        elif hasattr(exc, "error_message"):
            server_errors.append(exc.error_message)
        else:
            pass

        return server_errors

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        server_errors = format_exception(exc)

        return templates.TemplateResponse(
            template,
            {
                "request": request,
                "server_errors": server_errors,
                "title": "New Message",
            },
        )

    @app.exception_handler(429)
    async def custom_429_handler(request, exc):
        server_errors = format_exception(exc)
        server_errors = (
            server_errors
            if server_errors
            else ["Too many requests, please try again later"]
        )
        return templates.TemplateResponse(
            template,
            {
                "request": request,
                "server_errors": server_errors,
                "title": "New Message",
            },
        )

    @app.exception_handler(500)
    async def custom_500_handler(request, __):
        server_errors: List = [
            "Something seems to be broken. Please contact admin for assistance"
        ]

        return templates.TemplateResponse(
            template,
            {
                "request": request,
                "server_errors": server_errors,
                "title": "New Message",
            },
        )

    @app.exception_handler(404)
    async def custom_404_handler(request, exc):
        server_errors = format_exception(exc)

        return templates.TemplateResponse(
            template,
            {
                "request": request,
                "server_errors": server_errors,
                "title": "New Message",
            },
        )

    @app.exception_handler(401)
    async def custom_401_handler(request, exc):
        server_errors = format_exception(exc)

        return templates.TemplateResponse(
            "auth/templates/login.html",
            {"request": request, "server_errors": server_errors, "title": "Login"},
        )
