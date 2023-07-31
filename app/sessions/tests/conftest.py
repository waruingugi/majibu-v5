import pytest
from sqlalchemy.orm import Session
from pytest_mock import MockerFixture

from app.sessions.daos.session import duo_session_dao


@pytest.fixture
def delete_duo_session_model_instances(db: Session) -> None:
    """Delete previously existing rows in DuoSession model"""
    existing_duo_sessions = duo_session_dao.get_all(db)
    for duo_session in existing_duo_sessions:
        duo_session_dao.remove(db, id=duo_session.id)


@pytest.fixture
def mock_user_has_sufficient_balance(db: Session, mocker: MockerFixture) -> None:
    """Mock has_sufficient_balance function to return true in utils"""
    mocker.patch(
        "app.sessions.utils.has_sufficient_balance",
        return_value=True,
    )
