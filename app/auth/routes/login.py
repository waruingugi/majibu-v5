from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.core.deps import get_db

from app.auth.utils import templates
from app.auth.serializers.auth import FormatPhoneSerializer, CreateTOTPSerializer
from app.auth.otp import create_otp  # noqa
from app.notifications.daos.notifications import notifications_dao  # noqa

router = APIRouter()


@router.get("/validate-phone/", response_class=HTMLResponse)
async def get_phone_verification(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/validate-phone/", response_class=HTMLResponse)
async def post_phone_verification(
    request: Request,
    db: Session = Depends(get_db),
    phone_in: FormatPhoneSerializer = Depends(),
):
    if phone_in.is_valid():
        """Save the phone to the session.
        This ensures the same user proceeds to the verification page."""
        request.session["phone"] = phone_in.phone
        create_otp_data = CreateTOTPSerializer(phone=phone_in.phone)  # noqa

        # notifiaction_in = create_otp(create_otp_data)
        # notifications_dao.send_notification(db, obj_in=notifiaction_in)

    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/validate-otp/", response_class=HTMLResponse)
async def get_otp_verification(request: Request):
    return templates.TemplateResponse(
        "login.html", {"request": request, "phone": request.session["phone"]}
    )


# redirect

# Validate phone no
# On post, create OTP, send OTP
# save number to redis
# Save otp secret, e.t.c to redis
# Redirect to verify otp
# On OTP post, fetch redis
# If valid, generate access token
# redirect to home page
# If not valid, return to validation page
