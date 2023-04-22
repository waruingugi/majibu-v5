from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.core.deps import get_db

from app.core.config import templates
from app.auth.serializers.auth import (  # noqa
    FormatPhoneSerializer,
    CreateOTPSerializer,
    OTPSerializer,
)
from app.auth.otp import create_otp  # noqa
from app.notifications.daos.notifications import notifications_dao  # noqa

router = APIRouter()
template_prefix = "auth/templates/"


@router.get("/validate-phone/", response_class=HTMLResponse)
async def get_phone_verification(request: Request):
    return templates.TemplateResponse(
        f"{template_prefix}login.html", {"request": request}
    )


@router.post("/validate-phone/", response_class=HTMLResponse)
async def post_phone_verification(
    request: Request,
    db: Session = Depends(get_db),
    phone_in: FormatPhoneSerializer = Depends(),
):
    if phone_in.is_valid():
        create_otp_data = CreateOTPSerializer(phone=phone_in.phone)  # noqa

        notifiaction_in = create_otp(create_otp_data)
        notifications_dao.send_notification(db, obj_in=notifiaction_in)

        redirect_url = request.url_for("get_otp_verification", phone=phone_in.phone)
        return RedirectResponse(redirect_url, status_code=302)

    return templates.TemplateResponse(
        f"{template_prefix}login.html",
        {"request": request, "field_errors": phone_in.field_errors},
    )


@router.get("/validate-otp/{phone}", response_class=HTMLResponse)
async def get_otp_verification(
    request: Request,
    phone: str,
):
    return templates.TemplateResponse(
        f"{template_prefix}verification.html", {"request": request, "phone": phone}
    )


@router.post("/validate-otp/{phone}", response_class=HTMLResponse)
async def post_otp_verification(
    request: Request, phone: str, otp_in: OTPSerializer = Depends()
):
    if otp_in.is_valid():
        pass

    return templates.TemplateResponse(
        f"{template_prefix}verification.html", {"request": request}
    )


# DAO

# Validate phone no
# On post, create OTP, send OTP
# save number to redis
# Save otp secret, e.t.c to redis
# Redirect to verify otp
# On OTP post, fetch redis
# If valid, generate access token
# redirect to home page
# If not valid, return to validation page
