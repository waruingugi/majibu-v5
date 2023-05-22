from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from app.users.models import User
from sqlalchemy.orm import Session
from app.accounts.daos.account import transaction_dao
from app.commons.constants import Categories
from app.core.config import templates, settings
from app.core.deps import get_current_active_user_or_none, get_db
from app.core.ratelimiter import limiter
from app.core.logger import LoggingRoute


router = APIRouter(route_class=LoggingRoute)
template_prefix = "sessions/templates/"


@router.get("/home/", response_class=HTMLResponse)
@limiter.limit("5/minute")
async def get_home(
    request: Request,
):
    """Get home page"""
    return templates.TemplateResponse(
        f"{template_prefix}home.html",
        {"request": request, "title": "Home", "categories": Categories.list_()},
    )


@router.get("/preferred-redirect/", response_class=HTMLResponse)
async def get_preferred_redirect(
    request: Request,
):
    """Redirect to a preferred page otherwise go to homepage"""
    redirect_url = request.cookies.get(
        "preferred_redirect_to", request.url_for("get_home")
    )

    return RedirectResponse(redirect_url, status_code=302)


@router.get("/summary/{category}", response_class=HTMLResponse)
async def get_summary(
    request: Request,
    category: str,
    user: User = Depends(get_current_active_user_or_none),
    db: Session = Depends(get_db),
):
    """Display session summary"""
    has_sufficient_balance = False
    wallet_balance = 0.0

    # If user is logged in, check if they have sufficient balance to proceed
    if user is not None:
        wallet_balance = transaction_dao.get_user_balance(db, account=user.phone)
        has_sufficient_balance = wallet_balance >= settings.SESSION_AMOUNT

    return templates.TemplateResponse(
        f"{template_prefix}summary.html",
        {
            "request": request,
            "title": "Summary",
            "category": category,
            "is_logged_in": False if user is None else True,
            "has_sufficient_balance": has_sufficient_balance,
            "wallet_balance": wallet_balance,
        },
    )
