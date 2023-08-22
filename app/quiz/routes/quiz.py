from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.users.models import User

from app.quiz.utils import GetSessionQuestions
from app.quiz.utils import CalculateScore
from app.quiz.daos.quiz import result_dao
from app.core.config import templates
from app.core.deps import (
    get_current_active_user,
    get_db,
)
from app.core.logger import LoggingRoute


router = APIRouter(route_class=LoggingRoute)
template_prefix = "quiz/templates/"


@router.get("/questions/{result_id}", response_class=HTMLResponse)
async def get_questions(
    request: Request,
    result_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
    get_session_questions=Depends(GetSessionQuestions),
):
    """Get questions and choices page"""
    # quiz = get_session_questions(result_id=result_id)
    quiz = [
        {
            "id": "fdcddb3e-9c97-4c56-b38a-bce474dab82a",
            "question_text": "070e07aa-8e09-46ae-b34a-21deb514d289",
            "choices": [
                {
                    "id": "b28dc380-b4b2-4ac9-8f43-e5a41d9c8bfb",
                    "question_id": "fdcddb3e-9c97-4c56-b38a-bce474dab82a",
                    "choice_text": "7d1f5622-fc45-4dd9-9f89-bc7ae6d30e04",
                },
                {
                    "id": "3ccafaf7-ae3f-4f09-9fdb-190a6dbd1ecb",
                    "question_id": "fdcddb3e-9c97-4c56-b38a-bce474dab82a",
                    "choice_text": "0c5921e7-e03b-4946-99ad-ea5250e48178",
                },
                {
                    "id": "fa7dc4ff-fb63-4496-9225-8760ce3dedf8",
                    "question_id": "fdcddb3e-9c97-4c56-b38a-bce474dab82a",
                    "choice_text": "e5217a92-5157-4fc0-968f-65c05ae720c9",
                },
            ],
        },
        {
            "id": "34553b30-29a2-4320-b16e-cf326e41494d",
            "question_text": "55509bf2-a29a-41fa-bed3-887f1c328317",
            "choices": [
                {
                    "id": "4edd5978-e07d-4cc3-b93f-e85646dee1c8",
                    "question_id": "34553b30-29a2-4320-b16e-cf326e41494d",
                    "choice_text": "0fcd2c03-0051-496d-bc18-6010ff48a1b1",
                },
                {
                    "id": "f79bfb16-bfd8-4a61-adaf-f609d928c94a",
                    "question_id": "34553b30-29a2-4320-b16e-cf326e41494d",
                    "choice_text": "9377b0d6-78f7-48c3-a61f-7f2ea5829ee0",
                },
                {
                    "id": "27c14b76-118e-44d8-a12a-78856c2b4d07",
                    "question_id": "34553b30-29a2-4320-b16e-cf326e41494d",
                    "choice_text": "eefdc12d-c358-4054-a57d-282f01999305",
                },
            ],
        },
        {
            "id": "f278704a-6df5-4bca-bf8b-521c449db344",
            "question_text": "93bc36f4-0e92-46cf-ada8-4bceec3fc840",
            "choices": [
                {
                    "id": "ba870029-9973-47a1-9716-4e34a8e33328",
                    "question_id": "f278704a-6df5-4bca-bf8b-521c449db344",
                    "choice_text": "9f6e4e1a-8c63-4bf3-911e-1a62310d55ac",
                },
                {
                    "id": "f5dee9fc-89cf-4b87-a8dd-a7f09c9eb62f",
                    "question_id": "f278704a-6df5-4bca-bf8b-521c449db344",
                    "choice_text": "95738642-9ca1-454e-90e5-b1e58e6649cd",
                },
                {
                    "id": "79d27400-4a1a-44ba-b772-ac5f995b730b",
                    "question_id": "f278704a-6df5-4bca-bf8b-521c449db344",
                    "choice_text": "cad1b6cd-b12f-48d1-bd5f-0db6f084bddf",
                },
            ],
        },
        {
            "id": "61d81303-3d82-4679-a89f-f22d5715ce86",
            "question_text": "2cd5792f-a819-41c9-8204-767be199978d",
            "choices": [
                {
                    "id": "9cba5cf8-af35-4d6d-b5a8-bb565f80c71a",
                    "question_id": "61d81303-3d82-4679-a89f-f22d5715ce86",
                    "choice_text": "b8f5826b-1fdf-4d3a-87a3-1cf740e90f4e",
                },
                {
                    "id": "fb40e7c6-7bd0-4b86-99c6-dec88f16de79",
                    "question_id": "61d81303-3d82-4679-a89f-f22d5715ce86",
                    "choice_text": "62e63b21-7d95-4531-a74c-a7f4394a348e",
                },
                {
                    "id": "a0ed0236-5382-41e6-9a1e-b03ca789d93f",
                    "question_id": "61d81303-3d82-4679-a89f-f22d5715ce86",
                    "choice_text": "50d2a625-ea5c-48ed-af68-793fbfe99c97",
                },
            ],
        },
        {
            "id": "82757f57-bd13-4c08-accc-08aea1c20cbe",
            "question_text": "6f9b103f-4ac0-4242-b181-f8e73eeca4ce",
            "choices": [
                {
                    "id": "c350eaeb-2077-4e2f-96c1-c3a43ba91788",
                    "question_id": "82757f57-bd13-4c08-accc-08aea1c20cbe",
                    "choice_text": "d89a376d-06a2-4923-b147-9ca8c223253d",
                },
                {
                    "id": "74f45a95-7cc8-4a1b-8b66-9f1e82f00778",
                    "question_id": "82757f57-bd13-4c08-accc-08aea1c20cbe",
                    "choice_text": "950799d5-f7b4-447d-a41d-cc69cd8cce49",
                },
                {
                    "id": "70c54977-c68f-4889-85c9-6f8001f007d5",
                    "question_id": "82757f57-bd13-4c08-accc-08aea1c20cbe",
                    "choice_text": "9d672423-7723-4910-aca6-a4c2c7b8273b",
                },
            ],
        },
    ]

    return templates.TemplateResponse(
        f"{template_prefix}questions.html",
        {"request": request, "title": "Quiz", "quiz": quiz},
    )


@router.post("/answers/{result_id}", response_class=HTMLResponse)
async def post_answers(
    request: Request,
    result_id: str,
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_active_user),
    # get_session_questions=Depends(GetSessionQuestions),
    calculate_score=Depends(CalculateScore),
):
    """POST answers to API, calculate the score then redirect to results page"""
    # form_data = await request.form()

    # calculate_score(form_data._dict)
    quiz = [
        {
            "id": "fdcddb3e-9c97-4c56-b38a-bce474dab82a",
            "question_text": "070e07aa-8e09-46ae-b34a-21deb514d289",
            "choices": [
                {
                    "id": "b28dc380-b4b2-4ac9-8f43-e5a41d9c8bfb",
                    "question_id": "fdcddb3e-9c97-4c56-b38a-bce474dab82a",
                    "choice_text": "7d1f5622-fc45-4dd9-9f89-bc7ae6d30e04",
                },
                {
                    "id": "3ccafaf7-ae3f-4f09-9fdb-190a6dbd1ecb",
                    "question_id": "fdcddb3e-9c97-4c56-b38a-bce474dab82a",
                    "choice_text": "0c5921e7-e03b-4946-99ad-ea5250e48178",
                },
                {
                    "id": "fa7dc4ff-fb63-4496-9225-8760ce3dedf8",
                    "question_id": "fdcddb3e-9c97-4c56-b38a-bce474dab82a",
                    "choice_text": "e5217a92-5157-4fc0-968f-65c05ae720c9",
                },
            ],
        },
        {
            "id": "34553b30-29a2-4320-b16e-cf326e41494d",
            "question_text": "55509bf2-a29a-41fa-bed3-887f1c328317",
            "choices": [
                {
                    "id": "4edd5978-e07d-4cc3-b93f-e85646dee1c8",
                    "question_id": "34553b30-29a2-4320-b16e-cf326e41494d",
                    "choice_text": "0fcd2c03-0051-496d-bc18-6010ff48a1b1",
                },
                {
                    "id": "f79bfb16-bfd8-4a61-adaf-f609d928c94a",
                    "question_id": "34553b30-29a2-4320-b16e-cf326e41494d",
                    "choice_text": "9377b0d6-78f7-48c3-a61f-7f2ea5829ee0",
                },
                {
                    "id": "27c14b76-118e-44d8-a12a-78856c2b4d07",
                    "question_id": "34553b30-29a2-4320-b16e-cf326e41494d",
                    "choice_text": "eefdc12d-c358-4054-a57d-282f01999305",
                },
            ],
        },
        {
            "id": "f278704a-6df5-4bca-bf8b-521c449db344",
            "question_text": "93bc36f4-0e92-46cf-ada8-4bceec3fc840",
            "choices": [
                {
                    "id": "ba870029-9973-47a1-9716-4e34a8e33328",
                    "question_id": "f278704a-6df5-4bca-bf8b-521c449db344",
                    "choice_text": "9f6e4e1a-8c63-4bf3-911e-1a62310d55ac",
                },
                {
                    "id": "f5dee9fc-89cf-4b87-a8dd-a7f09c9eb62f",
                    "question_id": "f278704a-6df5-4bca-bf8b-521c449db344",
                    "choice_text": "95738642-9ca1-454e-90e5-b1e58e6649cd",
                },
                {
                    "id": "79d27400-4a1a-44ba-b772-ac5f995b730b",
                    "question_id": "f278704a-6df5-4bca-bf8b-521c449db344",
                    "choice_text": "cad1b6cd-b12f-48d1-bd5f-0db6f084bddf",
                },
            ],
        },
        {
            "id": "61d81303-3d82-4679-a89f-f22d5715ce86",
            "question_text": "2cd5792f-a819-41c9-8204-767be199978d",
            "choices": [
                {
                    "id": "9cba5cf8-af35-4d6d-b5a8-bb565f80c71a",
                    "question_id": "61d81303-3d82-4679-a89f-f22d5715ce86",
                    "choice_text": "b8f5826b-1fdf-4d3a-87a3-1cf740e90f4e",
                },
                {
                    "id": "fb40e7c6-7bd0-4b86-99c6-dec88f16de79",
                    "question_id": "61d81303-3d82-4679-a89f-f22d5715ce86",
                    "choice_text": "62e63b21-7d95-4531-a74c-a7f4394a348e",
                },
                {
                    "id": "a0ed0236-5382-41e6-9a1e-b03ca789d93f",
                    "question_id": "61d81303-3d82-4679-a89f-f22d5715ce86",
                    "choice_text": "50d2a625-ea5c-48ed-af68-793fbfe99c97",
                },
            ],
        },
        {
            "id": "82757f57-bd13-4c08-accc-08aea1c20cbe",
            "question_text": "6f9b103f-4ac0-4242-b181-f8e73eeca4ce",
            "choices": [
                {
                    "id": "c350eaeb-2077-4e2f-96c1-c3a43ba91788",
                    "question_id": "82757f57-bd13-4c08-accc-08aea1c20cbe",
                    "choice_text": "d89a376d-06a2-4923-b147-9ca8c223253d",
                },
                {
                    "id": "74f45a95-7cc8-4a1b-8b66-9f1e82f00778",
                    "question_id": "82757f57-bd13-4c08-accc-08aea1c20cbe",
                    "choice_text": "950799d5-f7b4-447d-a41d-cc69cd8cce49",
                },
                {
                    "id": "70c54977-c68f-4889-85c9-6f8001f007d5",
                    "question_id": "82757f57-bd13-4c08-accc-08aea1c20cbe",
                    "choice_text": "9d672423-7723-4910-aca6-a4c2c7b8273b",
                },
            ],
        },
    ]

    return templates.TemplateResponse(
        f"{template_prefix}questions.html",
        {"request": request, "title": "Quiz", "quiz": quiz},
    )


@router.get("/score/{result_id}", response_class=HTMLResponse)
async def get_result_score(
    request: Request,
    result_id: str,
    db: Session = Depends(get_db),
):
    """Page is shown immediately after playing a session"""
    result = result_dao.get_not_none(db, id=result_id)

    return templates.TemplateResponse(
        f"{template_prefix}score.html",
        {
            "request": request,
            "title": "Your Score",
            "score": result.score,
            "expires_at": result.expires_at,
            "category": result.category,
        },
    )


# Remove docs
# Redirect template on quiz
# If withdraw balance bank is below, fail transactions

# On submission
# Check if time is valid, not expired
# If expired, raise can not be submitted due to time out
# If has been submitted before, raise error
# Calculate results, save to db
# Is active true column in results db: it means was played within last 30 minutes
# Once paired or refunded create duo session with appropriate status
