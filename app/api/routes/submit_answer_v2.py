import os
import uuid
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
import logging
from time import perf_counter

from fastapi import APIRouter, Depends, Request
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
from app.services.question_cache import get_exam_day_questions_cached
from app.services.exam_runtime_cache import exam_runtime_cache
from app.schemas.attempt import AttemptStartRequest, AttemptStartResponse
from app.schemas.answer import AnswerSubmitRequest, AnswerSubmitResponse

# ✅ NEW CONTRACT
from app.core.errors import forbidden, not_found, conflict
from app.core.error_codes import ErrorCode

from app.schemas._strict import StrictRequest
from datetime import timedelta

from sqlalchemy.dialects.postgresql import insert
from app.services.attempt_repository import AttemptRepository

# Allow small real-world tolerance
grace_seconds = 30


import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ==========================================================
# SUBMIT ANSWER
# ==========================================================
#from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

@router.post("/{attempt_id}/submit-answer-v2", response_model=AnswerSubmitResponse)
def submit_answer_v2(
    request: Request,
    attempt_id: UUID,
    payload: AnswerSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    now = datetime.now(timezone.utc)


    try:
        # ==========================================================
        # FETCH ATTEMPT (OPTIMIZED: JOINEDLOAD → avoids extra query)
        # ==========================================================
        result = (
            db.query(Attempt, Participant.user_id)
            .join(
                Participant,
                Participant.id == Attempt.participant_id,
            )
            .filter(Attempt.id == attempt_id)
            .with_for_update()
            .first()
        )

        if not result:
            not_found(
                ErrorCode.ATTEMPT_NOT_FOUND,
                "Attempt not found",
            )

        attempt, participant_user_id = result

        if participant_user_id != current_user.id:
            forbidden(
                ErrorCode.FORBIDDEN,
                "Unauthorized attempt access",
            )


        if attempt.status != AttemptStatus.IN_PROGRESS:

            forbidden(
                ErrorCode.ATTEMPT_NOT_ACTIVE,
                "Attempt is not active",
            )

        # ==========================================================
        # TIME CHECK
        # ==========================================================
        elapsed_seconds = int((now - attempt.started_at).total_seconds())

        if elapsed_seconds >= attempt.allowed_duration_seconds:
            finalize_attempt(db, attempt)
            db.commit()
            forbidden(ErrorCode.ATTEMPT_EXPIRED, "Attempt time expired")

        # ==========================================================
        # FETCH QUESTION FROM CACHE (NO DB HIT)
        # ==========================================================
        
        questions_map = get_exam_day_questions_cached(
            str(attempt.exam_day_id)
        )
        question = questions_map.get(
            str(payload.question_id)
        )

        if not question:
            not_found(
                ErrorCode.QUESTION_NOT_FOUND,
                "Question not found",
            )

        # ==========================================================
        # STAGE 4 — VALIDATE QUESTION
        # ==========================================================

        pool = attempt.question_pool_ids or {}
        allowed_ids = (
            set(pool.get("base", []))
            | set(pool.get("bonus", []))
        )

        if str(payload.question_id) not in allowed_ids:
            forbidden(
                ErrorCode.INVALID_QUESTION_ACCESS,
                "Question not part of attempt pool",
            )

        # ==========================================================
        # STAGE 5 — LOAD EXISTING ANSWER
        # ==========================================================


        existing_answer = (
            db.query(AttemptAnswer)
            .filter(
                AttemptAnswer.attempt_id == attempt.id,
                AttemptAnswer.question_id == payload.question_id,
            )
            .first()
        )

        # ==========================================================
        # PRECOMPUTED VALUES
        # ==========================================================

        existing_selected_option = (
            existing_answer.selected_option
            if existing_answer
            else ""
        )

        existing_hint_used_at = (
            existing_answer.hint_used_at
            if existing_answer
            else None
        )

        existing_first_hint_opened_at = (
            existing_answer.first_hint_opened_at
            if existing_answer
            else None
        )

        existing_time_to_first_hint_seconds = (
            existing_answer.time_to_first_hint_seconds
            if existing_answer
            else None
        )

        # ==========================================================
        # STAGE 6 — SCORE CALCULATION
        # ==========================================================


        hint_already_used = existing_answer.hint_used if existing_answer else False
        hint_used_final = hint_already_used or payload.hint_used

        selected = payload.selected_option

        if selected and "_" in selected:
            try:
                selected_key = selected.split("_")[-1]
            except Exception:
                selected_key = None
        else:
            selected_key = selected

        previous_selected = existing_selected_option
        current_selected = selected_key or ""


        answer_changed = (
            existing_answer is not None
            and previous_selected != current_selected
        )

        existing_change_count = (
            existing_answer.answer_change_count
            if existing_answer
            else 0
        )

        new_answer_change_count = (
            existing_change_count + 1
            if answer_changed
            else existing_change_count
        )

        is_correct = (
            selected_key is not None
            and selected_key == question["correct_option"]
        )

        weight = Decimal(str(question["weight"]))
        penalty_pct = Decimal(str(question["hint_penalty_percentage"]))

        raw_score = weight if is_correct else Decimal("0")
        effective_score = raw_score

        if is_correct and hint_used_final:
            penalty = raw_score * (penalty_pct / Decimal("100"))
            effective_score = raw_score - penalty

        # ==========================================================
        # PRECOMPUTED WRITE VALUES
        # ==========================================================

        increment_hint = (
            payload.hint_used
            and not hint_already_used
        )

        new_hints_used_count = (
            (attempt.hints_used_count or 0) + 1
            if increment_hint
            else (attempt.hints_used_count or 0)
        )

        if increment_hint:
            hint_used_at_value = now
            first_hint_opened_at_value = now

            time_to_first_hint_seconds_value = (
                int((now - attempt.started_at).total_seconds())
                if attempt.started_at
                else None
            )
        else:
            hint_used_at_value = existing_hint_used_at

            first_hint_opened_at_value = (
                existing_first_hint_opened_at
            )
            time_to_first_hint_seconds_value = (
                existing_time_to_first_hint_seconds
            )




        # ==========================================================
        # BUILD WRITE PAYLOADS
        # ==========================================================
        insert_values = {
            "attempt_id": attempt.id,
            "question_id": payload.question_id,
            "selected_option": selected_key or "",
            "is_correct": is_correct,
            "hint_used": hint_used_final,
            "hint_used_at": hint_used_at_value,
            "answered_at": now,
            "raw_score": raw_score,
            "effective_score": effective_score,
            "is_special": question["is_special"],
            "weight_used": weight,
            "first_hint_opened_at": first_hint_opened_at_value,
            "time_to_first_hint_seconds": time_to_first_hint_seconds_value,
            "answer_change_count":0,
        }

        update_values = {
            "selected_option": (
                selected_key
                if selected_key is not None
                else existing_selected_option
            ),
            "is_correct": is_correct,
            "hint_used": hint_used_final,
            "answered_at": now,
            "raw_score": raw_score,
            "effective_score": effective_score,
            "hint_used_at": hint_used_at_value,
            "first_hint_opened_at": first_hint_opened_at_value,
            "time_to_first_hint_seconds": time_to_first_hint_seconds_value,
            "answer_change_count": new_answer_change_count,
            "updated_at": func.now(),
        }

        stmt = (
            insert(AttemptAnswer)
            .values(**insert_values)
            .on_conflict_do_update(
                index_elements=["attempt_id", "question_id"],
                set_=update_values,
            )
        )

        response_payload = AnswerSubmitResponse(
            is_correct=is_correct,
            raw_score=float(raw_score),
            effective_score=float(effective_score),
            total_hints_used=new_hints_used_count,
        )

        db.execute(stmt)
        
        # ==========================================================
        # HINT COUNTER (UNCHANGED LOGIC)
        # ==========================================================
        if increment_hint:
            attempt.hints_used_count = new_hints_used_count

        db.commit()

        return response_payload

    except IntegrityError:
        db.rollback()
        conflict(ErrorCode.DATABASE_ERROR, "Answer submission conflict")

    except Exception:
        db.rollback()
        raise
