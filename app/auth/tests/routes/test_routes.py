from fastapi.testclient import TestClient
from app.core.config import settings
from pytest_mock import MockerFixture


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


def test_post_phone_verification_fails(client: TestClient, mocker: MockerFixture):
    mocker.patch(
        "app.auth.routes.login.notifications_dao.send_notification",
        return_value=None,
    )
    response = client.post("/auth/validate-phone/", data={"phone": "wrong"})

    assert response.template.name == "auth/templates/login.html"
    assert response.context["field_errors"] is not None


def test_get_otp_verification(client: TestClient):
    response = client.get("/auth/validate-otp/" + settings.SUPERUSER_PHONE)
    assert response.status_code == 200
    assert response.template.name == "auth/templates/verification.html"
