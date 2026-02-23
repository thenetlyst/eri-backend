import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.question import Question
from app.schemas.question import QuestionCreate, QuestionResponse
from app.models.user import User

router = APIRouter(prefix="/questions", tags=["Question Admin"])


@router.post("/", response_model=QuestionResponse)
def create_question(
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = Question(
        id=uuid.uuid4(),
        challenge_id=payload.challenge_id,
        exam_day_id=payload.exam_day_id,
        question_order=payload.question_order,
        question_text=payload.question_text,
        option_a=payload.option_a,
        option_b=payload.option_b,
        option_c=payload.option_c,
        option_d=payload.option_d,
        correct_option=payload.correct_option,
        weight=payload.weight,
        difficulty=payload.difficulty,
        allocated_time_seconds=payload.allocated_time_seconds,
        hint_text=payload.hint_text,
        hint_penalty_percentage=payload.hint_penalty_percentage,
        is_special=payload.is_special,
    )

    db.add(q)
    db.commit()
    db.refresh(q)

    return q