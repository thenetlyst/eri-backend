from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.question import Question
from app.services.attempt_snapshot_service import build_attempt_snapshot

router = APIRouter()


@router.get("/{attempt_id}/reconstruct")
def reconstruct_attempt(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = (
        db.query(Attempt)
        .filter(Attempt.id == attempt_id)
        .first()
    )

    if not attempt:
        raise HTTPException(
            status_code=404,
            detail="Attempt not found",
        )

    # 🔒 Ownership check
    if attempt.participant.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized access to attempt",
        )

    # Fetch answers
    answers = (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt.id)
        .all()
    )

    # Fetch questions
    questions = (
        db.query(Question)
        .filter(Question.exam_day_id == attempt.exam_day_id)
        .order_by(Question.question_order)
        .all()
    )

    snapshot = build_attempt_snapshot(
        attempt=attempt,
        questions=questions,
        answers=answers,
    )

    return {
        "attempt_id": attempt.id,
        "status": attempt.status,
        "allowed_duration_seconds": attempt.allowed_duration_seconds,
        "snapshot": snapshot,
    }