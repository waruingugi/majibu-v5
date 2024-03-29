from fastapi import Request, APIRouter, Depends, BackgroundTasks, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.core.deps import get_current_active_user_or_none, get_db
from app.core.security import get_access_token

from app.core.config import templates
from app.core.logger import LoggingRoute
from app.auth.serializers.auth import (  # noqa
    FormatPhoneSerializer,
    CreateOTPSerializer,
    OTPSerializer,
    ValidateOTPSerializer,
)
from app.auth.otp import create_otp, validate_otp  # noqa
from app.notifications.daos.notifications import notifications_dao  # noqa
from app.users.daos.user import user_dao
from app.users.serializers.user import UserCreateSerializer
from app.users.models import User
from app.errors.custom import ErrorCodes
from app.core.security import insert_token_in_cookie
from app.core.ratelimiter import limiter


router = APIRouter(route_class=LoggingRoute)
template_prefix = "auth/templates/"


@router.get("/validate-phone/", response_class=HTMLResponse)
async def get_phone_verification(request: Request):
    """Get login html"""
    return templates.TemplateResponse(
        f"{template_prefix}login.html", {"request": request, "title": "Login"}
    )


@router.post("/validate-phone/", response_class=HTMLResponse)
@limiter.limit("5/minute")
async def post_phone_verification(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    phone_in: FormatPhoneSerializer = Depends(),
):
    """Receive POST to validate phone number"""
    if phone_in.is_valid():
        user = user_dao.get_or_create(db, UserCreateSerializer(phone=phone_in.phone))
        user_is_active = user_dao.is_active(user)

        if user_is_active:
            create_otp_data = CreateOTPSerializer(phone=phone_in.phone)  # noqa

            notifiaction_in = create_otp(create_otp_data)

            background_tasks.add_task(
                notifications_dao.send_notification, db, obj_in=notifiaction_in
            )

            redirect_url = request.url_for("get_otp_verification", phone=phone_in.phone)
            return RedirectResponse(redirect_url, status_code=302)
        else:
            phone_in.field_errors.append(ErrorCodes.INACTIVE_ACCOUNT.value)

    return templates.TemplateResponse(
        f"{template_prefix}login.html",
        {"request": request, "title": "Login", "field_errors": phone_in.field_errors},
    )


@router.get("/validate-otp/{phone}", response_class=HTMLResponse)
async def get_otp_verification(
    request: Request,
    phone: str,
):
    """Get verification template"""
    return templates.TemplateResponse(
        f"{template_prefix}verification.html",
        {"request": request, "phone": phone, "title": "Verification"},
    )


@router.post("/validate-otp/{phone}", response_class=HTMLResponse)
async def post_otp_verification(
    request: Request,
    phone: str,
    otp_in: OTPSerializer = Depends(),
    db: Session = Depends(get_db),
):
    """Receive POST and validates OTP is valid"""
    data = ValidateOTPSerializer(otp=otp_in.otp, phone=phone)

    if validate_otp(data):
        user = user_dao.get_not_none(db, phone=phone)
        token_obj = get_access_token(db, user_id=user.id)

        cookie = insert_token_in_cookie(token_obj)

        redirect_url = request.cookies.get(
            "preferred_redirect_to", request.url_for("get_home")
        )

        response = RedirectResponse(
            redirect_url, status_code=302, headers={"Set-Cookie": cookie}
        )

        # Additional in-secure cookie to check that user is logged in
        response.set_cookie(key="is_logged_in", value="True", httponly=False)
        return response
    else:
        otp_in.field_errors.append(ErrorCodes.INVALID_OTP.value)

    return templates.TemplateResponse(
        f"{template_prefix}verification.html",
        {
            "request": request,
            "field_errors": otp_in.field_errors,
            "title": "Verification",
        },
    )


@router.get("/logout", response_class=HTMLResponse)
async def logout(
    request: Request,
    response: Response,
    _: User = Depends(get_current_active_user_or_none),
):
    """Log out the current user"""
    # response.set_cookie(key="access_token", value="", max_age=1)
    # response.delete_cookie("access_token", domain="localhost")
    response = templates.TemplateResponse(
        f"{template_prefix}login.html",
        {"request": request, "title": "Login"},
    )
    response.delete_cookie("access_token")
    response.delete_cookie("is_logged_in")

    return response
