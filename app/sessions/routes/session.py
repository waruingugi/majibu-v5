from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Callable
from http import HTTPStatus

from app.sessions.serializers.session import SessionCategoryFormSerializer
from app.sessions.utils import GetAvailableSession
from app.users.models import User
from app.accounts.daos.account import transaction_dao
from app.commons.constants import Categories
from app.core.config import templates, settings
from app.core.deps import (
    get_current_active_user_or_none,
    get_current_active_user,
    get_db,
    business_is_open,
)
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
    business_is_open: Callable = Depends(business_is_open),
):
    """Display session summary"""
    float_is_sufficient = False
    wallet_balance = 0.0

    # If user is logged in, check if they have sufficient balance to proceed
    if user is not None:
        wallet_balance = transaction_dao.get_user_balance(db, account=user.phone)
        float_is_sufficient = wallet_balance >= settings.SESSION_AMOUNT

    return templates.TemplateResponse(
        f"{template_prefix}summary.html",
        {
            "request": request,
            "title": "Summary",
            "is_logged_in": False if user is None else True,
            "has_sufficient_balance": float_is_sufficient,
            "wallet_balance": wallet_balance,
            "categories": Categories.list_(),
            "business_opens_at": settings.BUSINESS_OPENS_AT,
            "business_closes_at": settings.BUSINESS_CLOSES_AT,
            "business_is_open": business_is_open,
            "session_amount": settings.SESSION_AMOUNT,
            "session_fee": settings.SESSION_FEE,
        },
    )


@router.post("/summary/", response_class=HTMLResponse)
async def post_session(
    request: Request,
    category_in: SessionCategoryFormSerializer = Depends(),
    business_is_open: Callable = Depends(business_is_open),
    user: User = Depends(get_current_active_user),
    get_available_session: GetAvailableSession = Depends(GetAvailableSession),
):
    if business_is_open:
        get_available_session(category=category_in.category, user=user)

    # Invalid or fishy request, so we logout the user
    # They shouldn't be able to post if business is closed
    return RedirectResponse(
        request.url_for("logout"), status_code=HTTPStatus.FOUND.value
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


# @router.get("/off-business-hours/", response_class=HTMLResponse)
# async def off_business_hours(
#     request: Request,
# ):
#     """Show page when user tries to play outside business hours"""
#     return templates.TemplateResponse(
#         f"{template_prefix}off_business_hours.html",
#         {
#             "request": request,
#             "title": "Please try again later",
#             "business_opens_at": settings.BUSINESS_OPENS_AT,
#             "business_closes_at": settings.BUSINESS_CLOSES_AT,
#         },
#     )


# Remove docs
# Submit form
# Submit form test
# Check user has sufficient balance *
# Check redis has no user withdrawals in queue *
# Check user has no active session
# Check if session category is available:
# If not raise error
# If it is choose same session id in session
# Atomic block
# Deduct balance, save to redis deduction
# Autofill results with null values
# Set in session has(user + session id) for 30 minutes
# Saved values in redis are: user_id, session_id, expire_time(no submissions from user),
# Redirect to questions page


# On submission
# Check if time is valid, not expired
# If expired, raise can not be submitted due to time out
# Calculate results, save to db
# Is active true column in results db: it means was played within last 30 minutes
# Once paired or refunded create duo session with appropriate status
