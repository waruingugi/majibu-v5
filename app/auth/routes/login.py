from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.auth.utils import templates
from app.auth.serializers.auth import FormatPhoneSerializer

router = APIRouter()


@router.get("/validate-phone/", response_class=HTMLResponse)
async def get_phone_verification(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/validate-phone/", response_class=HTMLResponse)
async def post_phone_verificationin(
    request: Request, phone_in: FormatPhoneSerializer = Depends()
):
    if phone_in.is_valid():
        # Save to redis
        pass

    return templates.TemplateResponse("login.html", {"request": request})


# Send notifications module: Hostpinnacle
# Test notifications model -> user, test notification dao
# Add notification to check spam folder
# Create notifications dao
# Under dao send sms func
# Callback

# Validate phone no
# On post, create OTP, send OTP
# save number to redis
# Save otp secret, e.t.c to redis
# Redirect to verify otp
# On OTP post, fetch redis
# If valid, generate access token
# redirect to home page
# If not valid, return to validation page