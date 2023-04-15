class SendQuickHPKSms:
    pass


# @singleton
# class SendHighPriorityATSms:
#     @inject
#     def __init__(self, notifications_dao: NotificationsDao) -> None:
#         self.notifications_dao = notifications_dao

#     def __call__(
#         self,
#         db: Session,
#         *,
#         message: str,
#         recipient_id: Optional[str] = None,
#         user_id: Optional[str] = None,
#     ) -> None:
#         notification = GlobalNotificationCreateSerializer(
#             recipient_id=recipient_id,
#             user_id=user_id,
#             message=message,
#             channel=NotificationChannels.SMS.value,
#             provider=NotificationProviders.AFRICAS_TALKING.value,
#             priority=NotificationPriorities.HIGH.value,
#         )
#         self.notifications_dao.send_notification(db, obj_in=notification)
