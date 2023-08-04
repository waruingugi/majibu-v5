from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI

from app.auth import api as auth_api
from app.sessions import api as sessions_api
from app.accounts import api as accounts_api
from app.quiz import api as quiz_api

# Withouth this code, celery throws a few errors
from app.core.celery_app import celery  # noqa

from app.core.ratelimiter import limiter
from app.exceptions.handlers import register_exception_handlers

from asgi_correlation_id import CorrelationIdMiddleware

# Rate limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


app = FastAPI()

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CorrelationIdMiddleware)


app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth_api.router)
app.include_router(sessions_api.router)
app.include_router(accounts_api.router)
app.include_router(quiz_api.router)

register_exception_handlers(app)
