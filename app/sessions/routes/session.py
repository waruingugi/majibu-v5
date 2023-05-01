from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.core.config import templates
from app.users.models import User
from app.core.deps import get_current_active_user
from app.core.ratelimiter import limiter
from app.commons.constants import Categories


router = APIRouter()
template_prefix = "sessions/templates/"


@router.get("/home/", response_class=HTMLResponse)
@limiter.limit("5/minute")
async def get_home(
    request: Request,
    _: User = Depends(get_current_active_user),
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
):
    """Display session summary"""
    return templates.TemplateResponse(
        f"{template_prefix}summary.html",
        {"request": request, "title": "Summary", "category": category},
    )


# Create templates
# Opening soon template run on close
# Request logger
# Top banner to join whatsapp group - comming soon
# No more sessions
# Host on heroku, buy domain
# Create models
# Create tests
# Create serializers
