from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.api.deps import get_db, get_current_user
from app.models.exam_day import ExamDay
from app.models.user import User
from app.models.participant import Participant
from app.models.attempt import Attempt

router = APIRouter(tags=["Exam Status"])


@router.get("/exam/status")
def get_exam_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)

    exam_day = (
        db.query(ExamDay)
        .order_by(ExamDay.created_at.desc())
        .first()
    )

    if not exam_day:
        return {
            "window_state": "AFTER_WINDOW",
            "server_time": now.isoformat(),
            "window_start": None,
            "window_end": None,
            "exam_day_id": None,
            "attempt": None,
        }

    # -----------------------------
    # Window State
    # -----------------------------

    if exam_day.is_force_locked:
        window_state = "FORCE_LOCKED"

    elif now < exam_day.window_start:
        window_state = "BEFORE_WINDOW"

    elif exam_day.window_start <= now <= exam_day.window_end:
        window_state = "WINDOW_OPEN"

    else:
        window_state = "AFTER_WINDOW"

    # -----------------------------
    # Participant
    # -----------------------------

    participant = (
        db.query(Participant)
        .filter(Participant.user_id == current_user.id)
        .order_by(Participant.created_at.desc())
        .first()
    )

    attempt_data = None

    if participant:
        attempt = (
            db.query(Attempt)
            .filter(Attempt.participant_id == participant.id)
            .order_by(Attempt.created_at.desc())
            .first()
        )

        if attempt:
            attempt_data = {
                "id": str(attempt.id),
                "status": attempt.status,
            }

    return {
        "window_state": window_state,
        "server_time": now.isoformat(),
        "window_start": exam_day.window_start.isoformat(),
        "window_end": exam_day.window_end.isoformat(),
        "exam_day_id": str(exam_day.id),
        "attempt": attempt_data,
    }