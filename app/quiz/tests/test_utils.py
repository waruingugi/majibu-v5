from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
from datetime import datetime, timedelta
from typing import Callable
import pytest

from app.core.config import settings
from app.users.daos.user import user_dao
from app.quiz.serializers.quiz import ResultCreateSerializer
from app.quiz.daos.quiz import result_dao, choice_dao, user_answer_dao
from app.quiz.utils import GetSessionQuestions, CalculateScore
from app.sessions.daos.session import session_dao
from app.commons.constants import Categories
from app.exceptions.custom import SessionExpired, LateSessionSubmission


def test_get_session_questions_if_past_expiry_time(
    db: Session,
    mocker: MockerFixture,
    create_super_user_instance: Callable,
    create_session_instance: Callable,
    delete_result_model_instances: Callable,
):
    """Test that the class GetSessionQuestions fails if called past result expiry time"""
    mock_datetime = mocker.patch("app.quiz.utils.datetime")
    mock_datetime.now.return_value = datetime.now() + timedelta(
        seconds=settings.SESSION_DURATION + 1
    )
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    session = session_dao.get_not_none(db, category=Categories.BIBLE.value)

    result_in = ResultCreateSerializer(user_id=user.id, session_id=session.id)
    result_obj = result_dao.create(db, obj_in=result_in)

    with pytest.raises(SessionExpired):
        get_session_questions = GetSessionQuestions(db, user)
        _ = get_session_questions(result_id=result_obj.id)


def test_get_questions_returns_correct_db_instances(
    db: Session,
    mocker: MockerFixture,
    create_super_user_instance: Callable,
    create_question_model_instances: Callable,
    delete_result_model_instances: Callable,
):
    """Test that the function get_questions() returns correct db instances"""
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    session = session_dao.get_not_none(db, category=Categories.BIBLE.value)

    result_in = ResultCreateSerializer(user_id=user.id, session_id=session.id)
    result_dao.create(db, obj_in=result_in)

    get_session_questions = GetSessionQuestions(db, user)
    get_session_questions.session_obj = session

    questions_obj = get_session_questions.get_questions()

    for question in questions_obj:
        assert question.id in session.questions

    assert len(questions_obj) == settings.QUESTIONS_IN_SESSION


def test_get_choices_returns_correct_db_instances(
    db: Session,
    create_super_user_instance: Callable,
    create_question_model_instances: Callable,
    delete_result_model_instances: Callable,
) -> None:
    """Test that the function get_choices() returns correct db instances"""
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    session = session_dao.get_not_none(db, category=Categories.BIBLE.value)

    result_in = ResultCreateSerializer(user_id=user.id, session_id=session.id)
    result_dao.create(db, obj_in=result_in)

    get_session_questions = GetSessionQuestions(db, user)
    get_session_questions.session_obj = session

    choices_obj = get_session_questions.get_choices()
    choice_ids = [choice.choice_text for choice in choice_dao.get_all(db)]

    for choice in choices_obj:
        assert choice.id in choice_ids


def test_compose_quiz_returns_correct_list(
    db: Session,
    mocker: MockerFixture,
    create_super_user_instance: Callable,
    create_choice_model_instances: Callable,
    delete_result_model_instances: Callable,
) -> None:
    """Test that the function compoze_quiz returns correct db instances"""
    mock_datetime = mocker.patch("app.quiz.utils.datetime")
    mock_datetime.now.return_value = datetime.now() - timedelta(
        seconds=settings.SESSION_DURATION
    )
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    session = session_dao.get_not_none(db, category=Categories.BIBLE.value)

    result_in = ResultCreateSerializer(user_id=user.id, session_id=session.id)
    result_obj = result_dao.create(db, obj_in=result_in)

    get_session_questions = GetSessionQuestions(db, user)

    quiz = get_session_questions(result_id=result_obj.id)
    choices = [choice for choice in choice_dao.get_all(db)]

    assert quiz is not None
    assert len(quiz) == settings.QUESTIONS_IN_SESSION

    for quiz_object in quiz:
        choices = quiz_object["choices"]

        for choice in choices:
            assert quiz_object["id"] == choice["question_id"]
            assert quiz_object["question_text"] is not None
            assert choice["choice_text"] is not None


def test_session_submitted_in_time_raises_exception(
    db: Session,
    mocker: MockerFixture,
    create_super_user_instance: Callable,
    create_choice_model_instances: Callable,
    delete_result_model_instances: Callable,
) -> None:
    """Assert the function raises an exception if the session is submitted 1 second
    past the buffer time"""
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    session = session_dao.get_not_none(db, category=Categories.BIBLE.value)

    result_in = ResultCreateSerializer(user_id=user.id, session_id=session.id)
    result_obj = result_dao.create(db, obj_in=result_in)

    mock_datetime = mocker.patch("app.quiz.utils.datetime")
    mock_datetime.now.return_value = result_obj.expires_at + timedelta(
        seconds=settings.SESSION_BUFFER_TIME + 1
    )

    with pytest.raises(LateSessionSubmission):
        calculate_score = CalculateScore(db, user)
        _ = calculate_score(form_data={}, result_id=result_obj.id, user=user)


def test_create_user_answers_creates_model_instances(
    db: Session,
    mocker: MockerFixture,
    create_super_user_instance: Callable,
    create_choice_model_instances: Callable,
) -> None:
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    session = session_dao.get_not_none(db, category=Categories.BIBLE.value)

    result_in = ResultCreateSerializer(user_id=user.id, session_id=session.id)
    result_obj = result_dao.create(db, obj_in=result_in)

    form_data = {}

    for question_id in session.questions:
        choice = choice_dao.get_not_none(db, question_id=question_id)
        form_data[choice.question_id] = choice.id

    calculate_score = CalculateScore(db, user)
    _ = calculate_score(form_data=form_data, result_id=result_obj.id, user=user)

    user_answers = user_answer_dao.get_all(db, session_id=session.id, user_id=user.id)
    assert len(user_answers) == settings.QUESTIONS_IN_SESSION
