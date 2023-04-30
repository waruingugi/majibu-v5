from typing import List

from fastapi import FastAPI
from app.auth import api as auth_api
from app.sessions import api as session_api
from app.core.config import templates
from fastapi.staticfiles import StaticFiles

from starlette.exceptions import HTTPException as StarletteHTTPException


# Rate limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.ratelimiter import limiter


app = FastAPI()

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth_api.router)
app.include_router(session_api.router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    server_errors: List = []

    if hasattr(exc, "detail"):
        server_errors.append(exc.detail)
    if hasattr(exc, "error_message"):
        server_errors.append(exc.error_message)

    return templates.TemplateResponse(
        "templates/info.html",
        {"request": request, "server_errors": server_errors, "title": "New Message"},
    )


@app.exception_handler(429)
async def custom_429_handler(request, __):
    server_errors: List = ["Too many requests, please try again later"]
    return templates.TemplateResponse(
        "templates/info.html",
        {"request": request, "server_errors": server_errors, "title": "New Message"},
    )


@app.exception_handler(404)
async def custom_404_handler(request, __):
    server_errors: List = ["The requested page could not be found"]
    return templates.TemplateResponse(
        "templates/info.html",
        {"request": request, "server_errors": server_errors, "title": "New Message"},
    )


@app.exception_handler(401)
async def custom_401_handler(request, __):
    server_errors: List = []
    return templates.TemplateResponse(
        "auth/templates/login.html",
        {"request": request, "server_errors": server_errors, "title": "Login"},
    )
