from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.sessions.serializers.session import SessionCategoryFormSerializer
from app.users.models import User
from app.accounts.daos.account import transaction_dao
from app.commons.constants import Categories
from app.core.config import templates, settings
from app.core.deps import get_current_active_user_or_none, get_db
from app.core.logger import LoggingRoute


router = APIRouter(route_class=LoggingRoute)
template_prefix = "sessions/templates/"


# @router.get("/home/", response_class=HTMLResponse)
# @limiter.limit("5/minute")
# async def get_home(
#     request: Request,
# ):
#     """Get home page"""
#     return templates.TemplateResponse(
#         f"{template_prefix}home.html",
#         {"request": request, "title": "Home", "categories": Categories.list_()},
#     )


@router.get("/home/", response_class=HTMLResponse)
async def get_home(
    request: Request,
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
            "is_logged_in": False if user is None else True,
            "has_sufficient_balance": has_sufficient_balance,
            "wallet_balance": wallet_balance,
            "categories": Categories.list_(),
        },
    )


@router.post("/summary/", response_class=HTMLResponse)
async def post_session(
    request: Request,
    category: SessionCategoryFormSerializer,
):
    """Redirect to a preferred page otherwise go to homepage"""
    redirect_url = request.cookies.get(
        "preferred_redirect_to", request.url_for("get_home")
    )

    return RedirectResponse(redirect_url, status_code=302)


@router.get("/preferred-redirect/", response_class=HTMLResponse)
async def get_preferred_redirect(
    request: Request,
):
    """Redirect to a preferred page otherwise go to homepage"""
    redirect_url = request.cookies.get(
        "preferred_redirect_to", request.url_for("get_home")
    )

    return RedirectResponse(redirect_url, status_code=302)


# JS check balance
# Remove docs
# Submit form
# Check if user has an active session
# Check if session category is available
# If not available choose random session in category user has not played
# If availabe choose same session id
# If no availabe, raise no available session error
# Check balance is sufficient and no recent withdrawals
# Deduct from wallet balance
# Auto fill results with null values
# Set in session has(user + session id) for 30 minutes
# Saved values in redis are: user_id, session_id, expire_time(no submissions from user),
# Redirect to questions page

# On submission
# Check if time is valid, not expired
# If expired, raise can not be submitted due to time out
# Calculate results, save to db
# Is active true column in results db: it means was played within last 30 minutes
# Once paired or refunded create duo session with appropriate status
