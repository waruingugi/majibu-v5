from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI

from app.auth import api as auth_api
from app.sessions import api as session_api

from asgi_correlation_id import CorrelationIdMiddleware


# Rate limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.ratelimiter import limiter
from app.exceptions.handlers import register_exception_handlers


app = FastAPI()

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CorrelationIdMiddleware)


app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth_api.router)
app.include_router(session_api.router)

register_exception_handlers(app)
