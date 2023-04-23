from app.auth.serializers.token import TokenCreateSerializer, TokenInDBSerializer
from app.db.dao import CRUDDao
from app.auth.models import AuthToken
from app.core.raw_logger import logger
from sqlalchemy.orm import Session
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError


class TokenDao(CRUDDao[AuthToken, TokenCreateSerializer, TokenInDBSerializer]):
    def on_pre_create(
        self, db: Session, id: str, values: dict, orig_values: dict
    ) -> None:
        """
        Tasks to run before creating a new token instance:
        1. Change token_type from a serializer object to a string type
        2. Set previous tokens assigned to user to false. This prevents the tokens
        from being re-used.
        """
        logger.info(f"Invalidating previous tokens before creating token id: {id}")
        # 1.
        values["token_type"] = orig_values["token_type"].value

        # 2.
        stmt = (
            update(self.model.__table__)
            .where(self.model.user_id == orig_values["user_id"])
            .values(is_active=False)
        )
        db.execute(stmt)

        try:
            db.commit()
        except IntegrityError as integrity_error:
            logger.exception(
                f"Encountered exception while pre-creating token: {integrity_error}"
            )
            db.rollback()
            raise


token_dao = TokenDao(AuthToken)
