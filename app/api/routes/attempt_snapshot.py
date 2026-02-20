from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.models.attempt import Attempt
from app.models.question import Question
from app.models.attempt_answer import AttemptAnswer
from app.services.attempt_snapshot_service import build_attempt_snapshot


# ----------------------------------------------------------
# Router
# ----------------------------------------------------------

router = APIRouter(
    prefix="/attempts",
    tags=["Attempts"],
)


# ----------------------------------------------------------
# Snapshot Endpoint
# ----------------------------------------------------------

@router.get("/{attempt_id}/snapshot")
def get_attempt_snapshot(
    attempt_id: UUID,
    db: Session = Depends(get_db),
):

    # ------------------------------------------------------
    # Fetch attempt
    # ------------------------------------------------------

    attempt = (
        db.query(Attempt)
        .filter(Attempt.id == attempt_id)
        .first()
    )

    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    # ------------------------------------------------------
    # Fetch ordered questions
    # ------------------------------------------------------

    questions = (
        db.query(Question)
        .filter(Question.challenge_id == attempt.challenge_id)
        .order_by(Question.question_order)
        .all()
    )

    # ------------------------------------------------------
    # Fetch answers
    # ------------------------------------------------------

    answers = (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt.id)
        .all()
    )

    # ------------------------------------------------------
    # Build snapshot
    # ------------------------------------------------------

    snapshot = build_attempt_snapshot(
        attempt=attempt,
        questions=questions,
        answers=answers,
    )

    return snapshot