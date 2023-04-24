from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.core.security import get_access_token

from app.core.config import templates
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
from app.errors.custom import ErrorCodes


router = APIRouter()
template_prefix = "auth/templates/"


@router.get("/validate-phone/", response_class=HTMLResponse)
async def get_phone_verification(request: Request):
    """Get login html"""

    return templates.TemplateResponse(
        f"{template_prefix}login.html", {"request": request}
    )


@router.post("/validate-phone/", response_class=HTMLResponse)
async def post_phone_verification(
    request: Request,
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
            notifications_dao.send_notification(db, obj_in=notifiaction_in)

            redirect_url = request.url_for("get_otp_verification", phone=phone_in.phone)
            return RedirectResponse(redirect_url, status_code=302)
        else:
            phone_in.field_errors.append(ErrorCodes.INACTIVE_ACCOUNT.value)

    return templates.TemplateResponse(
        f"{template_prefix}login.html",
        {"request": request, "field_errors": phone_in.field_errors},
    )


@router.get("/validate-otp/{phone}", response_class=HTMLResponse)
async def get_otp_verification(
    request: Request,
    phone: str,
):
    """Get verification template"""
    return templates.TemplateResponse(
        f"{template_prefix}verification.html", {"request": request, "phone": phone}
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

        cookie: str = f"access_token=Bearer {token_obj.access_token}; path=/;"
        return templates.TemplateResponse(
            "sessions/templates/home.html",
            {"request": request},
            headers={"Set-Cookie": cookie},
        )

    return templates.TemplateResponse(
        f"{template_prefix}verification.html", {"request": request}
    )


# If valid, generate access token
# Get or create user
# TokenDao, TokenSerializers
# Ecommerce security get_access_token
# Send message on background task
# Validate otp on expire
# Set cookie http only,
# raise InvalidToken fix this <--
# raise ExpiredAccessToken  <--
# raise IncorrectCredentials <---
# raise InactiveAccount <----
# raise InsufficientUserPrivileges <---
# Response
# Throttling
# redirect to home page
# If not valid, return to validation page
