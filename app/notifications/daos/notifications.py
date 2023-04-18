from sqlalchemy.orm import Session
from app.db.dao import CRUDDao
from app.notifications.models import Notification
from app.notifications.serializers.notifications import (
    CreateNotificationSerializer,
    UpdateNotificationSerializer,
)
from app.notifications.constants import (
    NotificationStatuses,
    NotificationChannels,
    NotificationProviders,
)
from app.notifications.utils import HPKSms


class NotificationsDao(
    CRUDDao[Notification, CreateNotificationSerializer, UpdateNotificationSerializer]
):
    def send_notification(
        self, db: Session, *, obj_in: CreateNotificationSerializer
    ) -> Notification:
        db_obj = self.create(db, obj_in=obj_in)

        if obj_in.channel == NotificationChannels.SMS.value:
            # Handle HostPinnacle sms notifications
            if obj_in.provider == NotificationProviders.HOST_PINNACLE.value:
                self.send_hpk_sms(db, db_obj=db_obj)

        return db_obj

    def send_hpk_sms(self, db: Session, db_obj: Notification) -> None:
        response = HPKSms.send_quick_sms(
            phone=db_obj.phone,
            message=db_obj.message,
        )

        if response and (response.get("status", None) == "success"):
            self.update(
                db, db_obj=db_obj, obj_in={"status": NotificationStatuses.SENT.value}
            )

        else:
            self.update(
                db, db_obj=db_obj, obj_in={"status": NotificationStatuses.FAILED.value}
            )


notifications_dao = NotificationsDao(Notification)
