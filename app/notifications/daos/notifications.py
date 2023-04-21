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
from app.notifications.utils import HPKSms, MobiTechSms


class NotificationsDao(
    CRUDDao[Notification, CreateNotificationSerializer, UpdateNotificationSerializer]
):
    def update_notification_status(self, db: Session, db_obj, response) -> None:
        if response and (response.get("status", None) == "success"):
            self.update(
                db, db_obj=db_obj, obj_in={"status": NotificationStatuses.SENT.value}
            )

        else:
            self.update(
                db, db_obj=db_obj, obj_in={"status": NotificationStatuses.FAILED.value}
            )

    def send_notification(
        self, db: Session, *, obj_in: CreateNotificationSerializer
    ) -> Notification:
        db_obj = self.create(db, obj_in=obj_in)

        if obj_in.channel == NotificationChannels.SMS.value:
            # Handle HostPinnacle sms notifications
            if obj_in.provider == NotificationProviders.HOST_PINNACLE.value:
                self.send_hpk_sms(db, db_obj=db_obj)

            # Handle MobiTech sms notifications
            if obj_in.provider == NotificationProviders.MOBI_TECH.value:
                self.send_mobitech_sms(db, db_obj=db_obj)

        return db_obj

    def send_hpk_sms(self, db: Session, db_obj: Notification) -> None:
        response = HPKSms.send_quick_sms(
            phone=db_obj.phone,
            message=db_obj.message,
        )

        self.update_notification_status(db, db_obj, response)

    def send_mobitech_sms(self, db: Session, db_obj: Notification) -> None:
        response = MobiTechSms.send_quick_sms(
            phone=db_obj.phone,
            message=db_obj.message,
        )

        self.update_notification_status(db, db_obj, response)


notifications_dao = NotificationsDao(Notification)
