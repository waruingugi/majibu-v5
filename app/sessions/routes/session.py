from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.core.config import templates
from app.users.models import User
from app.core.deps import get_current_active_user_or_none
from app.core.ratelimiter import limiter
from app.core.logger import LoggingRoute
from app.commons.constants import Categories


router = APIRouter(route_class=LoggingRoute)
template_prefix = "sessions/templates/"


@router.get("/home/", response_class=HTMLResponse)
@limiter.limit("5/minute")
async def get_home(
    request: Request,
    # _: User = Depends(get_current_active_user),
):
    """Get home page"""
    return templates.TemplateResponse(
        f"{template_prefix}home.html",
        {"request": request, "title": "Home", "categories": Categories.list_()},
    )


@router.get("/summary/{category}", response_class=HTMLResponse)
async def get_summary(
    request: Request,
    category: str,
    user: User = Depends(get_current_active_user_or_none),
):
    """Display session summary"""
    return templates.TemplateResponse(
        f"{template_prefix}summary.html",
        {
            "request": request,
            "title": "Summary",
            "category": category,
            "is_logged_in": False if user is None else True,
        },
    )


# Navbar Account balance
# logout
# Clean tests
# Account - mpesa
# Protect docs
# Opening soon template run on close
# Request logger
# Top banner to join whatsapp group - comming soon
# No more sessions
# Host on heroku, buy domain
# Create models
# Create tests
# Create serializers
