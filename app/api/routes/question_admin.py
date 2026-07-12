import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_db, get_current_user
from app.models.question import Question
from app.schemas.question import QuestionCreate, QuestionResponse
from app.models.user import User
from app.core.exceptions import ConflictException

router = APIRouter(tags=["Question Admin"])


@router.post("/", response_model=QuestionResponse)
def create_question(
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ==========================================================
    # 🔒 NORMALIZE + VALIDATE CORRECT OPTION
    # ==========================================================
    correct_option = payload.correct_option.strip().upper()

    if correct_option not in ["A", "B", "C", "D"]:
        raise ValueError("correct_option must be one of A, B, C, D")

    # ==========================================================
    # 🔒 OPTIONAL: VALIDATE content_json OPTIONS (SAFE GUARD)
    # ==========================================================
    if payload.content_json and isinstance(payload.content_json, dict):
        options = payload.content_json.get("options")

        if options:
            valid_keys = {"A", "B", "C", "D"}

            for opt in options:
                key = opt.get("key")
                if key not in valid_keys:
                    raise ValueError(
                        f"Invalid option key in content_json: {key}"
                    )

    # ==========================================================
    # 🧱 CREATE QUESTION
    # ==========================================================
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

        # 🔥 USE NORMALIZED VALUE
        correct_option=correct_option,

        weight=payload.weight,
        difficulty=payload.difficulty,
        allocated_time_seconds=payload.allocated_time_seconds,

        hint_text=payload.hint_text,
        hint_penalty_percentage=payload.hint_penalty_percentage,

        is_special=payload.is_special,
        content_json=payload.content_json,
    )

    db.add(q)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictException("Question already exists for this exam day")

    db.refresh(q)

    return q