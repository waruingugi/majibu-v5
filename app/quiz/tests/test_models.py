from sqlalchemy.orm import Session

from app.commons.constants import Categories
from app.quiz.daos.quiz import question_dao, choice_dao, answer_dao
from app.quiz.serializers.quiz import (
    QuestionCreateSerializer,
    ChoiceCreateSerializer,
    AnswerCreateSerializer,
)


def test_create_question(db: Session) -> None:
    """Test question can be created successfully"""
    question_text = "Random question"
    question_in = QuestionCreateSerializer(
        question_text=question_text, category=Categories.FOOTBALL.value
    )
    question = question_dao.create(db, obj_in=question_in)

    assert question.question_text == question_text
    assert question.category == Categories.FOOTBALL.value


def test_update_question(db: Session) -> None:
    """Test question can be updated successfully"""
    invalid_question = "Invalid question"
    question = question_dao.create(
        db,
        obj_in=QuestionCreateSerializer(
            question_text=invalid_question, category=Categories.FOOTBALL.value
        ),
    )

    updated_question = question_dao.update(
        db, db_obj=question, obj_in={"question_text": "Valid question"}
    )

    assert updated_question.question_text == "Valid question"
    assert updated_question.category == Categories.FOOTBALL.value


def test_create_choice(db: Session) -> None:
    """Test create question"""
    question_in = QuestionCreateSerializer(
        question_text="Random question", category=Categories.FOOTBALL.value
    )
    question = question_dao.create(db, obj_in=question_in)

    choice_text = "Choice text"
    choice = choice_dao.create(
        db,
        obj_in=ChoiceCreateSerializer(question_id=question.id, choice_text=choice_text),
    )

    assert choice.choice_text == choice_text
    assert choice.question_id == question.id


def test_create_answer(db: Session) -> None:
    """Test create answer"""
    question_in = QuestionCreateSerializer(
        question_text="Random question", category=Categories.FOOTBALL.value
    )
    question = question_dao.create(db, obj_in=question_in)

    choice = choice_dao.create(
        db,
        obj_in=ChoiceCreateSerializer(
            question_id=question.id, choice_text="Random choice"
        ),
    )

    answer = answer_dao.create(
        db, obj_in=AnswerCreateSerializer(question_id=question.id, choice_id=choice.id)
    )

    assert answer.choice_id == choice.id
    assert answer.question_id == question.id
