# Test db object is created
# Test notification is updated
# Test send sms func is called
# from sqlalchemy.orm import Session
# import pytest
# from pytest_mock import MockerFixture

# from app.notifications.serializers.notifications import CreateNotificationSerializer
# from app.notifications.daos.notifications import notifications_dao
# from app.core.config import settings


# def test_notification_dao_sends_sms(db: Session, mocker: MockerFixture) -> None:
#     mocked_response = {
#         "id": "67004999940",
#         "status_code": "200",
#         "status": "success",
#         "reason": "success",
#     }
#     mocker.patch(
#         "app.notifications.daos.notifications.HPKSms.send_quick_sms",
#         return_value=mocked_response
#     )
#     data_in = CreateNotificationSerializer(
#         type="OTP",
#         message="0976 is your OTP",
#         phone=settings.SUPERUSER_PHONE[1:],
#         provider="HOST_PINNACLE",
#         channel="SMS"
#     )
#     db_obj = notifications_dao.send_notification(
#         db, obj_in=data_in
#     )

#     assert db_obj is not None
