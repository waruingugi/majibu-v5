from pytest_mock import MockerFixture

from app.core.config import settings
from app.notifications.utils import HPKSms


def test_hpk_sms_returns_none_on_exception_raised(mocker: MockerFixture):
    mocker.patch("requests.post", side_effect=Exception("No internet!"))
    phone = settings.SUPERUSER_PHONE
    response = HPKSms.send_quick_sms(recipient=phone, message="test")

    assert response == {}
