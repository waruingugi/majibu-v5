from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Callable
from http import HTTPStatus

from app.sessions.serializers.session import SessionCategoryFormSerializer
from app.sessions.utils import view_session_history, GetAvailableSession, create_session
from app.users.models import User
from app.exceptions.custom import NoAvailabeSession
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
            "session_duration": settings.SESSION_DURATION,
        },
    )


@router.post("/summary/", response_class=HTMLResponse)
async def post_session(
    request: Request,
    category_in: SessionCategoryFormSerializer = Depends(),
    business_is_open: Callable = Depends(business_is_open),
    user: User = Depends(get_current_active_user),
    get_available_session: GetAvailableSession = Depends(GetAvailableSession),
    db: Session = Depends(get_db),
):
    """Post the session selected. Redirects to questions thereafter"""
    if business_is_open:
        session_id = get_available_session(category=category_in.category, user=user)

        if session_id is not None:
            result_id = create_session(db, user=user, session_id=session_id)

            return RedirectResponse(
                request.url_for("get_questions", result_id=result_id),
                status_code=HTTPStatus.FOUND.value,
            )
        else:
            raise NoAvailabeSession

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


@router.get("/history/", response_class=HTMLResponse)
async def get_sessions_history(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Get summarized history of all the sessions played"""
    sessions_history = view_session_history(db, user=user)

    # from datetime import datetime
    # sessions_history = [
    #     {
    #         "created_at": datetime.now(),
    #         "category": 'BIBLE',
    #         "session_id": "fga73nkkka",
    #         "status": 'REFUNDED',
    #         "party_a": {
    #             "id": "jkha439yphqhwoioe",
    #             "phone": +254704845041,
    #             "score": 74.56
    #         }
    #     },
    #     {
    #         "created_at": datetime.now(),
    #         "category": 'FOOTBALL',
    #         "session_id": "fga73nkkka",
    #         "status": 'PARTIALLY_REFUNDED',
    #         "party_a": {
    #             "id": "jkha439yphqhwoioe",
    #             "phone": +254704845041,
    #             "score": 0.00
    #         }
    #     },
    #     {
    #         "created_at": datetime.now(),
    #         "category": 'BIBLE',
    #         "session_id": "fga73nkkka",
    #         "status": 'WON',
    #         "party_a": {
    #             "id": "jkha439yphqhwoioe",
    #             "phone": +254704845041,
    #             "score": 74.56
    #         },
    #         "party_b": {
    #             "id": "jkha43987tqlwoioe",
    #             "phone": +254704845041,
    #             "score": 74.54
    #         },
    #     },
    #     {
    #         "created_at": datetime.now(),
    #         "category": 'BIBLE',
    #         "session_id": "fga73nkkka",
    #         "status": 'LOST',
    #         "party_a": {
    #             "id": "jkha439yphqhwoioe",
    #             "phone": +254704845041,
    #             "score": 74.54
    #         },
    #         "party_b": {
    #             "id": "jkha43987tqlwoioe",
    #             "phone": +254704845041,
    #             "score": 74.54
    #         },
    #     }
    # ]

    return templates.TemplateResponse(
        f"{template_prefix}history.html",
        {"request": request, "title": "History", "sessions_history": sessions_history},
    )
