import uuid
from datetime import datetime, timezone
from decimal import Decimal
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_db, get_current_user
from app.models.attempt import Attempt, AttemptStatus
from app.models.participant import Participant, AccountStatus
from app.models.exam_day import ExamDay
from app.models.question import Question
from app.models.attempt_answer import AttemptAnswer
from app.models.participant_progress import ParticipantProgress
from app.models.challenge import Challenge, ChallengeStatus
from app.models.user import User
from app.services.attempt_service import finalize_attempt
from app.schemas.attempt import AttemptStartRequest, AttemptStartResponse
from app.schemas.answer import AnswerSubmitRequest, AnswerSubmitResponse
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    ConflictException,
)
from app.services.attempt_event_service import (
    log_attempt_event,
    EVENT_ANSWER_CHANGED,
    EVENT_HINT_USED,
)

from pydantic import BaseModel
from app.services.attempt_event_service import (
    log_attempt_event,
    EVENT_QUESTION_VIEWED,
)

router = APIRouter(tags=["Attempts"])
logger = logging.getLogger(__name__)
class QuestionViewRequest(BaseModel):
    question_id: str

# ==========================================================
# START ATTEMPT
# ==========================================================

@router.post("/start", response_model=AttemptStartResponse)
def start_attempt(
    payload: AttemptStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    exam_day = db.query(ExamDay).filter(ExamDay.id == payload.exam_day_id).first()
    if not exam_day:
        raise NotFoundException("Exam day not found")

    challenge = db.query(Challenge).filter(
        Challenge.id == exam_day.challenge_id
    ).first()

    if not challenge:
        raise NotFoundException("Challenge not found")

    if challenge.status != ChallengeStatus.ACTIVE:
        raise ForbiddenException("Challenge not active")

    participant = (
        db.query(Participant)
        .filter(
            Participant.user_id == current_user.id,
            Participant.challenge_id == challenge.id,
        )
        .first()
    )

    if not participant:
        raise ForbiddenException("User not enrolled for this challenge")

    if participant.account_status != AccountStatus.ACTIVE:
        raise ForbiddenException("Participant account not active")

    now = datetime.now(timezone.utc)

    if now < exam_day.window_start or now > exam_day.window_end:
        raise ForbiddenException("Exam window not active")

    if exam_day.is_force_locked:
        raise ForbiddenException("Exam is force locked")

    existing_attempt = db.query(Attempt).filter(
        Attempt.participant_id == participant.id,
        Attempt.exam_day_id == exam_day.id
    ).first()

    if existing_attempt:
        raise ConflictException("Attempt already exists for this exam day")

    base_count = db.query(func.count(Question.id)).filter(
        Question.exam_day_id == exam_day.id,
        Question.is_special == False
    ).scalar()

    if base_count == 0:
        raise ForbiddenException("No base questions configured for this exam day")

    progress = db.query(ParticipantProgress).filter(
        ParticipantProgress.challenge_id == challenge.id,
        ParticipantProgress.participant_id == participant.id,
    ).first()

    special_unlocked = False
    if progress and progress.days_completed >= 2:
        special_unlocked = progress.eligible_for_bonus_next_day

    base_duration = db.query(
        func.coalesce(func.sum(Question.allocated_time_seconds), 0)
    ).filter(
        Question.exam_day_id == exam_day.id,
        Question.is_special == False
    ).scalar()

    special_duration = 0

    if special_unlocked:
        special_duration = db.query(
            func.coalesce(func.sum(Question.allocated_time_seconds), 0)
        ).filter(
            Question.exam_day_id == exam_day.id,
            Question.is_special == True
        ).scalar()

    total_allowed = int(base_duration + special_duration)

    attempt = Attempt(
        id=uuid.uuid4(),
        challenge_id=challenge.id,
        participant_id=participant.id,
        exam_day_id=exam_day.id,
        status=AttemptStatus.IN_PROGRESS,
        special_unlocked=special_unlocked,
        started_at=now,
        allowed_duration_seconds=total_allowed,
        hints_used_count=0,
        attendance_flag=True,
    )

    db.add(attempt)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictException("Attempt already exists")

    db.refresh(attempt)

    return AttemptStartResponse(
        attempt_id=attempt.id,
        allowed_duration_seconds=total_allowed,
        special_unlocked=special_unlocked,
    )


# ==========================================================
# SUBMIT ANSWER (RACE SAFE)
# ==========================================================

@router.post("/{attempt_id}/submit-answer", response_model=AnswerSubmitResponse)
def submit_answer(
    attempt_id: str,
    payload: AnswerSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    now = datetime.now(timezone.utc)

    attempt = (
        db.query(Attempt)
        .filter(Attempt.id == attempt_id)
        .with_for_update()
        .first()
    )

    if not attempt:
        raise NotFoundException("Attempt not found")

    if attempt.participant.user_id != current_user.id:
        raise ForbiddenException("Unauthorized attempt access")

    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise ForbiddenException("Attempt is not active")

    elapsed_seconds = int((now - attempt.started_at).total_seconds())

    if elapsed_seconds > attempt.allowed_duration_seconds:
        finalize_attempt(db, attempt)
        db.commit()
        raise ForbiddenException("Attempt time expired")

    question = db.query(Question).filter(
        Question.id == payload.question_id,
        Question.exam_day_id == attempt.exam_day_id,
    ).first()

    if not question:
        raise NotFoundException("Question not found")

    existing_answer = db.query(AttemptAnswer).filter(
        AttemptAnswer.attempt_id == attempt.id,
        AttemptAnswer.question_id == question.id,
    ).first()

    hint_already_used = existing_answer.hint_used if existing_answer else False
    hint_used_final = hint_already_used or payload.hint_used

    if payload.hint_used and not hint_already_used:
        attempt.hints_used_count += 1

    is_correct = payload.selected_option == question.correct_option
    raw_score = question.weight if is_correct else Decimal("0")
    effective_score = raw_score

    if is_correct and hint_used_final:
        penalty = raw_score * (
            question.hint_penalty_percentage / Decimal("100")
        )
        effective_score = raw_score - penalty

    try:
        if existing_answer:
            existing_answer.selected_option = payload.selected_option
            existing_answer.is_correct = is_correct
            existing_answer.hint_used = hint_used_final
            existing_answer.raw_score = raw_score
            existing_answer.effective_score = effective_score
            existing_answer.answered_at = now
        else:
            new_answer = AttemptAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option=payload.selected_option,
                is_correct=is_correct,
                hint_used=hint_used_final,
                hint_used_at=now if hint_used_final else None,
                answered_at=now,
                raw_score=raw_score,
                effective_score=effective_score,
            )
            db.add(new_answer)

        db.commit()

    except IntegrityError:
        db.rollback()

        existing_answer = db.query(AttemptAnswer).filter(
            AttemptAnswer.attempt_id == attempt.id,
            AttemptAnswer.question_id == question.id,
        ).first()

        if existing_answer:
            existing_answer.selected_option = payload.selected_option
            existing_answer.is_correct = is_correct
            existing_answer.hint_used = hint_used_final
            existing_answer.raw_score = raw_score
            existing_answer.effective_score = effective_score
            existing_answer.answered_at = now
            db.commit()

    # ==========================================================
    # EVENT LOGGING — ANSWER_CHANGED + HINT_USED
    # ==========================================================
    if attempt.status == AttemptStatus.IN_PROGRESS:
        log_attempt_event(
            db,
            attempt_id=attempt.id,
            question_id=question.id,
            event_type=EVENT_ANSWER_CHANGED,
        )

        if payload.hint_used and not hint_already_used:
            log_attempt_event(
                db,
                attempt_id=attempt.id,
                question_id=question.id,
                event_type=EVENT_HINT_USED,
            )

        db.commit()  # ⭐ critical — persist events

    return AnswerSubmitResponse(
        is_correct=is_correct,
        raw_score=float(raw_score),
        effective_score=float(effective_score),
        total_hints_used=attempt.hints_used_count,
    )

# ==========================================================
# FINALIZE ATTEMPT
# ==========================================================

@router.post("/{attempt_id}/finalize")
def finalize_attempt_endpoint(
    attempt_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    attempt = (
        db.query(Attempt)
        .filter(Attempt.id == attempt_id)
        .with_for_update()
        .first()
    )

    if not attempt:
        raise NotFoundException("Attempt not found")

    if attempt.participant.user_id != current_user.id:
        raise ForbiddenException("Unauthorized attempt access")

    if attempt.status == AttemptStatus.SUBMITTED:
        return {
            "message": "Attempt already finalized",
            "attempt_id": str(attempt.id),
            "raw_score": float(attempt.raw_score or 0),
            "final_score": float(attempt.final_score or 0),
        }

    finalize_attempt(db, attempt)
    db.commit()
    db.refresh(attempt)

    return {
        "message": "Attempt finalized successfully",
        "attempt_id": str(attempt.id),
        "raw_score": float(attempt.raw_score or 0),
        "final_score": float(attempt.final_score or 0),
        "total_time_seconds": attempt.total_time_seconds,
        "hints_used": attempt.hints_used_count,
    }


# ==========================================================
# RESUME ATTEMPT
# ==========================================================

@router.get("/{attempt_id}/resume")
def resume_attempt(
    attempt_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    now = datetime.now(timezone.utc)

    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()

    if not attempt:
        raise NotFoundException("Attempt not found")

    if attempt.participant.user_id != current_user.id:
        raise ForbiddenException("Unauthorized attempt access")

    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise ForbiddenException("Attempt is not active")

    elapsed = int((now - attempt.started_at).total_seconds())
    remaining = max(attempt.allowed_duration_seconds - elapsed, 0)

    answers = db.query(AttemptAnswer).filter(
        AttemptAnswer.attempt_id == attempt.id
    ).all()

    progress = [
        {
            "question_id": str(a.question_id),
            "selected_option": a.selected_option,
            "is_correct": a.is_correct,
            "hint_used": a.hint_used,
            "marked_for_review": a.marked_for_review,
        }
        for a in answers
    ]

    return {
        "attempt_id": str(attempt.id),
        "status": attempt.status,
        "remaining_time_seconds": remaining,
        "special_unlocked": attempt.special_unlocked,
        "hints_used": attempt.hints_used_count,
        "progress": progress,
    }
# ==========================================================
# HEARTBEAT (TELEMETRY ONLY)
# ==========================================================

@router.post("/{attempt_id}/heartbeat")
def heartbeat_attempt(
    attempt_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)

    attempt = (
        db.query(Attempt)
        .filter(Attempt.id == attempt_id)
        .with_for_update()
        .first()
    )

    if not attempt:
        raise NotFoundException("Attempt not found")

    if attempt.participant.user_id != current_user.id:
        raise ForbiddenException("Unauthorized attempt access")

    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise ForbiddenException("Attempt is not active")

    # update heartbeat timestamp
    attempt.last_heartbeat_at = now

    # compute remaining time
    elapsed = int((now - attempt.started_at).total_seconds())
    remaining = max(attempt.allowed_duration_seconds - elapsed, 0)

    db.commit()

    return {
        "attempt_id": str(attempt.id),
        "remaining_time_seconds": remaining,
        "status": attempt.status.value,
    }
# ==========================================================
# QUESTION VIEW EVENT
# ==========================================================

@router.post("/{attempt_id}/view-question")
def view_question(
    attempt_id: str,
    payload: QuestionViewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()

    if not attempt:
        raise NotFoundException("Attempt not found")

    if attempt.participant.user_id != current_user.id:
        raise ForbiddenException("Unauthorized")

    # lifecycle guard
    if attempt.status != AttemptStatus.IN_PROGRESS:
        return {"ok": True}

    import uuid
    print("VIEW EVENT FIRED", attempt.id, payload.question_id)
    log_attempt_event(
        db,
        attempt_id=attempt.id,
        question_id=payload.question_id,
        event_type=EVENT_QUESTION_VIEWED,
    )

    db.commit()

    return {"ok": True}