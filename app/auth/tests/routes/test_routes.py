from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from app.core.config import settings
from app.users.daos.user import user_dao
from app.users.serializers.user import UserCreateSerializer
from app.errors.custom import ErrorCodes


def test_get_phone_verification(client: TestClient):
    response = client.get("/auth/validate-phone/")
    assert response.status_code == 200
    assert response.template.name == "auth/templates/login.html"


def test_post_phone_verification(client: TestClient, mocker: MockerFixture):
    mocked_dao = mocker.patch(
        "app.auth.routes.login.notifications_dao.send_notification",
        return_value=None,
    )
    response = client.post(
        "/auth/validate-phone/", data={"phone": settings.SUPERUSER_PHONE}
    )
    mocked_dao.assert_called_once()
    assert response.template.name == "auth/templates/verification.html"
    assert response.context["phone"] == settings.SUPERUSER_PHONE


def test_post_phone_verification_fails_on_invalid_number(
    client: TestClient, mocker: MockerFixture
):
    mocker.patch(
        "app.auth.routes.login.notifications_dao.send_notification",
        return_value=None,
    )
    response = client.post("/auth/validate-phone/", data={"phone": "wrong"})

    assert response.template.name == "auth/templates/login.html"
    assert response.context["field_errors"] is not None


def test_post_phone_verification_fails_on_inactive_user(
    db: Session, client: TestClient, mocker: MockerFixture
):
    user = user_dao.get_or_create(
        db, obj_in=UserCreateSerializer(phone=settings.SUPERUSER_PHONE)
    )
    user_dao.update(db, db_obj=user, obj_in={"is_active": False})

    mocker.patch(
        "app.auth.routes.login.notifications_dao.send_notification",
        return_value=None,
    )
    response = client.post(
        "/auth/validate-phone/", data={"phone": settings.SUPERUSER_PHONE}
    )

    assert response.template.name == "auth/templates/login.html"
    assert response.context["field_errors"] == [ErrorCodes.INACTIVE_ACCOUNT.value]


def test_get_otp_verification(client: TestClient):
    response = client.get("/auth/validate-otp/" + settings.SUPERUSER_PHONE)
    assert response.status_code == 200
    assert response.template.name == "auth/templates/verification.html"


def test_post_otp_verification_fails_on_wrong_otp(client: TestClient):
    response = client.post(
        "/auth/validate-otp/" + settings.SUPERUSER_PHONE, data={"otp": "0987"}
    )
    assert response.context["field_errors"] == [ErrorCodes.INVALID_OTP.value]
    assert response.template.name == "auth/templates/verification.html"


def test_post_otp_verification_redirects_on_valid_otp(
    db: Session, client: TestClient, mocker: MockerFixture
):
    user_dao.get_or_create(
        db, obj_in=UserCreateSerializer(phone=settings.SUPERUSER_PHONE)
    )
    mocker.patch(
        "app.auth.routes.login.validate_otp",
        return_value=True,
    )
    response = client.post(
        "/auth/validate-otp/" + settings.SUPERUSER_PHONE, data={"otp": "0987"}
    )
    assert response.template.name == "sessions/templates/home.html"
