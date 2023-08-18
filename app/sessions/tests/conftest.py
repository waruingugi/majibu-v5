import pytest
from sqlalchemy.orm import Session
from pytest_mock import MockerFixture


@pytest.fixture
def mock_user_has_sufficient_balance(db: Session, mocker: MockerFixture) -> None:
    """Mock has_sufficient_balance function to return true in utils"""
    mocker.patch(
        "app.sessions.utils.has_sufficient_balance",
        return_value=True,
    )
