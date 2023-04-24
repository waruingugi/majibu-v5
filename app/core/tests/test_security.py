from app.core.security import get_access_token, insert_token_in_cookie
from app.users.daos.user import user_dao
from app.users.serializers.user import UserCreateSerializer
from app.core.config import settings

from sqlalchemy.orm import Session
from pytest_mock import MockerFixture


def test_localhost_inserts_token_in_cookie(db: Session):
    user = user_dao.get_or_create(
        db, obj_in=UserCreateSerializer(phone=settings.SUPERUSER_PHONE)
    )
    token_obj = get_access_token(db, user_id=user.id)
    cookie_with_token = insert_token_in_cookie(token_obj)

    secure_cookie_params = " Secure; HttpOnly"

    start_index = cookie_with_token.find("expires=") + len("expires=")
    end_index = cookie_with_token.find(";", start_index)
    token_eat = cookie_with_token[start_index:end_index]

    assert secure_cookie_params not in cookie_with_token
    assert token_eat == str(token_obj.access_token_eat)


def test_prod_inserts_token_in_cookie(db: Session, mocker: MockerFixture):
    mocker.patch(
        "app.core.security.settings.SQLALCHEMY_DATABASE_URI",
        return_value="db@prod-dummy-database-link",
    )
    user = user_dao.get_or_create(
        db, obj_in=UserCreateSerializer(phone=settings.SUPERUSER_PHONE)
    )
    token_obj = get_access_token(db, user_id=user.id)
    cookie_with_token = insert_token_in_cookie(token_obj)

    secure_cookie_params = " Secure; HttpOnly"

    assert secure_cookie_params in cookie_with_token
