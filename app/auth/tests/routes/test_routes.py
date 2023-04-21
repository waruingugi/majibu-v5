from fastapi.testclient import TestClient
from app.core.config import settings


def test_get_phone_verification(client: TestClient):
    response = client.get("/auth/validate-phone/")
    assert response.status_code == 200
    assert response.template.name == "auth/templates/login.html"


def test_phone_verification(client: TestClient):
    response = client.post(
        "/auth/validate-phone/", data={"phone": settings.SUPERUSER_PHONE}
    )
    assert response.template.name == "auth/templates/verification.html"
    assert response.context["phone"] == settings.SUPERUSER_PHONE
