from typing import List

from fastapi import FastAPI
from app.auth import api as auth_api
from app.sessions import api as session_api
from app.core.config import templates
from fastapi.staticfiles import StaticFiles

from starlette.exceptions import HTTPException as StarletteHTTPException


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth_api.router)
app.include_router(session_api.router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    field_errors: List = []

    if hasattr(exc, "detail"):
        field_errors.append(exc.detail)
    if hasattr(exc, "error_message"):
        field_errors.append(exc.error_message)

    return templates.TemplateResponse(
        "auth/templates/login.html",
        {"request": request, "field_errors": field_errors, "title": "New Message"},
    )
