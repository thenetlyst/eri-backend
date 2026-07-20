import os
import uuid
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
import logging
from time import perf_counter

from app.core.request_trace import RequestTrace

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

from app.services.attempt_event_service import (
    log_attempt_event,
    EVENT_ANSWER_CHANGED,
    EVENT_HINT_USED,
    EVENT_QUESTION_VIEWED,
)

from app.schemas._strict import StrictRequest
from datetime import timedelta

from sqlalchemy.dialects.postgresql import insert
from app.services.attempt_repository import AttemptRepository

# Allow small real-world tolerance
grace_seconds = 30



router = APIRouter(tags=["Attempts"])
logger = logging.getLogger(__name__)


class QuestionViewRequest(StrictRequest):
    question_id: UUID


# ==========================================================
# START ATTEMPT
# ==========================================================
@router.post("/start", response_model=AttemptStartResponse)
def start_attempt(
    request: Request,
    payload: AttemptStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy.dialects.postgresql import insert

    trace = RequestTrace(request)
    trace.mark_endpoint_start()
    request_start = perf_counter()

    connection_wait_start = None

    try:

        # ==========================================================
        # VALIDATIONS
        # ==========================================================
        connection_wait_start = perf_counter()

        with trace.measure("exam_day_lookup"):
            exam_day = AttemptRepository.get_exam_day(
                db,
                payload.exam_day_id,
            )

        connection_wait_ms = round(
            (perf_counter() - connection_wait_start) * 1000,
            2,
        )

        print("\n" + "=" * 60)
        print("FIRST DATABASE QUERY")
        print(f"Connection wait: {connection_wait_ms} ms")
        print(db.bind.pool.status())
        print("=" * 60 + "\n")


        logger.info(
            "first_query_completed",
            extra={
                "connection_wait_ms": connection_wait_ms,
                "pool_status": db.bind.pool.status(),
            },
        )

        if not exam_day:
            not_found(ErrorCode.ATTEMPT_NOT_FOUND, "Exam day not found")

        with trace.measure("challenge_lookup"):
            challenge = AttemptRepository.get_challenge(
                db,
                exam_day.challenge_id,
            )

        if not challenge:
            not_found(ErrorCode.ATTEMPT_NOT_FOUND, "Challenge not found")

        if challenge.status != ChallengeStatus.ACTIVE:
            forbidden(ErrorCode.FORBIDDEN, "Challenge not active")

   # print("----- DEBUG START -----")
   # print("current_user.id:", current_user.id)
   # print("type(current_user.id):", type(current_user.id))
   # print("challenge.id:", challenge.id)
   # print("type(challenge.id):", type(challenge.id))
   # print("----- DEBUG END -----")

        with trace.measure("participant_lookup"):
            participant = AttemptRepository.get_participant(
                db,
                user_id=current_user.id,
                challenge_id=challenge.id,
            )

        if not participant:
            logger.warning(
                "start_attempt_failed_validation",
                extra={
                    "stage": "participant_lookup",
                    "reason": "participant_not_found",
                    "total_ms": round((perf_counter() - request_start) * 1000, 2),
                    "trace": trace.summary(),
                },
            )

            forbidden(
                ErrorCode.FORBIDDEN,
                "User not enrolled for this challenge",
            )

        if participant.account_status != AccountStatus.ACTIVE:
            logger.warning(
                "start_attempt_failed_validation",
                extra={
                    "stage": "participant_lookup",
                    "reason": "participant_inactive",
                    "total_ms": round((perf_counter() - request_start) * 1000, 2),
                    "trace": trace.summary(),
                },
            )

            forbidden(
                ErrorCode.FORBIDDEN,
                "Participant account not active",
            )

        now = datetime.now(timezone.utc)

        if (
            now < exam_day.window_start - timedelta(seconds=grace_seconds)
            or now > exam_day.window_end + timedelta(seconds=grace_seconds)
        ):
            logger.warning(
                "start_attempt_failed_validation",
                extra={
                    "stage": "window_validation",
                    "reason": "window_closed",
                    "total_ms": round((perf_counter() - request_start) * 1000, 2),
                    "trace": trace.summary(),
                },
            )

            forbidden(
                ErrorCode.WINDOW_CLOSED,
                "Exam window not active",
            )

        if exam_day.is_force_locked:
            logger.warning(
                "start_attempt_failed_validation",
                extra={
                    "stage": "window_validation",
                    "reason": "force_locked",
                    "total_ms": round((perf_counter() - request_start) * 1000, 2),
                    "trace": trace.summary(),
                },
            )

            forbidden(
                ErrorCode.FORCE_LOCKED,
                "Exam is force locked",
            )

        # ==========================================================
        # PROGRESS
        # ==========================================================
        with trace.measure("progress_lookup"):
            progress = AttemptRepository.get_progress(
                db,
                participant_id=participant.id,
                challenge_id=challenge.id,
            )

        special_unlocked = False
        if progress and progress.days_completed >= 2:
            special_unlocked = progress.eligible_for_bonus_next_day

        # ==========================================================
        # QUESTIONS (CACHE)
        # ==========================================================
        with trace.measure("question_cache"):
            questions_map = get_exam_day_questions_cached(str(exam_day.id))

        questions = list(questions_map.values())

        base_ids = sorted([q["id"] for q in questions if not q["is_special"]])
        bonus_ids = sorted([q["id"] for q in questions if q["is_special"]])

        if not base_ids:
            logger.warning(
                "start_attempt_failed_validation",
                extra={
                    "stage": "question_cache",
                    "reason": "no_questions",
                    "total_ms": round((perf_counter() - request_start) * 1000, 2),
                    "trace": trace.summary(),
                },
            )

            forbidden(
                ErrorCode.INVALID_ATTEMPT,
                "No base questions configured for this exam day",
            )

        total_allowed = int(
            sum(
                q["allocated_time_seconds"]
                for q in questions
                if (not q["is_special"]) or special_unlocked
            )
        )

        seed = str(uuid.uuid4())

        # ==========================================================
        # 🔥 ATOMIC INSERT (OPTIMIZED)
        # ==========================================================
        stmt = insert(Attempt).values(
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
            shuffle_seed=seed,
            question_pool_ids={
                "base": base_ids,
                "bonus": bonus_ids,
            },
        )

        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_participant_exam_day"
        ).returning(
            Attempt.id,
            Attempt.allowed_duration_seconds,
            Attempt.special_unlocked,
            Attempt.status,
        )

        with trace.measure("db_write"):

            with trace.measure("attempt_insert"):
                result = db.execute(stmt)


            with trace.measure("returning_fetch"):
                row = result.fetchone()
    
            with trace.measure("flush"):
                db.flush()

            with trace.measure("commit"):
                db.commit()


        # ==========================================================
        # ✅ CASE 1: NEW ATTEMPT CREATED
        # ==========================================================
        if row:
            if row.status == AttemptStatus.SUBMITTED:
                forbidden(
                    ErrorCode.ALREADY_COMPLETED,
                    "Attempt already submitted",
                    meta={"attempt_id": str(row.id)}
                )
            
            with trace.measure("response_build"):
                response = AttemptStartResponse(
                    attempt_id=row.id,
                    allowed_duration_seconds=row.allowed_duration_seconds,
                    special_unlocked=row.special_unlocked,
                )

            total_ms = round((perf_counter() - request_start) * 1000, 2)

            logger.info(
                "start_attempt_profile",
                extra={
                    "participant_id": str(participant.id),
                    "attempt_created": True,
                    "total_ms": total_ms,
                    "connection_wait_ms": connection_wait_ms,
                    "pool_status": db.bind.pool.status(),
                    "trace": trace.summary(),
                },
            )
            print("\n" + "=" * 80)
            print("START_ATTEMPT PROFILE")
            print(f"Total: {total_ms} ms")
            print(f"Connection wait: {connection_wait_ms} ms")
            print(trace.summary())
            print("=" * 80 + "\n")


            return response

        # ==========================================================
        # ✅ CASE 2: EXISTING ATTEMPT (FALLBACK)
        # ==========================================================
        with trace.measure("existing_attempt_lookup"):
            attempt = (
                db.query(Attempt)
                .filter(
                    Attempt.participant_id == participant.id,
                    Attempt.exam_day_id == exam_day.id,
                )
                .first()
            )

        if not attempt:
            forbidden(
                ErrorCode.DATABASE_ERROR,
                "Failed to create or fetch attempt"
            )

        if attempt.status == AttemptStatus.SUBMITTED:
            forbidden(
                ErrorCode.ALREADY_COMPLETED,
                "Attempt already submitted",
                meta={"attempt_id": str(attempt.id)}
            )

        with trace.measure("response_build"):
            response = AttemptStartResponse(
                attempt_id=attempt.id,
                allowed_duration_seconds=attempt.allowed_duration_seconds,
                special_unlocked=attempt.special_unlocked,
            )

        total_ms = round((perf_counter() - request_start) * 1000, 2)

        logger.info(
            "start_attempt_profile",
            extra={
                "participant_id": str(participant.id),
                "attempt_created": False,
                "total_ms": total_ms,
                "connection_wait_ms": connection_wait_ms,
                "pool_status": db.bind.pool.status(),
                "trace": trace.summary(),
            },
        )
        print("\n" + "=" * 80)
        print("START_ATTEMPT FALLBACK")
        print(f"Total: {total_ms} ms")
        print(f"Connection wait: {connection_wait_ms} ms")
        print(trace.summary())
        print("=" * 80 + "\n")

        return response
    
    except Exception:
        total_ms = round((perf_counter() - request_start) * 1000, 2)

        logger.exception(
            "start_attempt_failed",
            extra={
                "total_ms": total_ms,
                "trace": trace.summary(),
            },
        )
        raise
    finally:
        trace.mark_endpoint_end()


# ==========================================================
# SUBMIT ANSWER
# ==========================================================
#from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

@router.post("/{attempt_id}/submit-answer", response_model=AnswerSubmitResponse)
def submit_answer(
    request: Request,
    attempt_id: UUID,
    payload: AnswerSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    trace = RequestTrace(request)
    trace.mark_endpoint_start()
    now = datetime.now(timezone.utc)

    # ✅ PRE-INITIALIZE
    is_active = False
    total_hints_used = 0

    try:
        # ==========================================================
        # FETCH ATTEMPT (OPTIMIZED: JOINEDLOAD → avoids extra query)
        # ==========================================================
        with trace.measure("attempt_lookup"):
            attempt = (
                db.query(Attempt)
                .options(joinedload(Attempt.participant))
                .filter(Attempt.id == attempt_id)
                .first()
            )

        if not attempt:
            not_found(ErrorCode.ATTEMPT_NOT_FOUND, "Attempt not found")

        if attempt.participant.user_id != current_user.id:
            forbidden(ErrorCode.FORBIDDEN, "Unauthorized attempt access")

        if attempt.status != AttemptStatus.IN_PROGRESS:
            logger.warning(
                "attempt_not_active",
                extra={
                    "attempt_id": str(attempt.id),
                    "status": attempt.status.value,
                    "worker_pid": os.getpid(),
                    **trace.summary(),
                },
            )

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
        
        with trace.measure("question_cache"):
            questions_map = get_exam_day_questions_cached(str(attempt.exam_day_id))
            question = questions_map.get(str(payload.question_id))

        if not question:
            not_found(ErrorCode.QUESTION_NOT_FOUND, "Question not found")

        # ==========================================================
        # VALIDATE QUESTION IN ATTEMPT POOL
        # ==========================================================
        with trace.measure("business_logic"):

            pool = attempt.question_pool_ids or {}
            allowed_ids = set(pool.get("base", [])) | set(pool.get("bonus", []))

            if str(payload.question_id) not in allowed_ids: 
                forbidden(
                    ErrorCode.INVALID_QUESTION_ACCESS,
                    "Question not part of attempt pool",
                )

            # ==========================================================
            # EXISTING ANSWER
            # ==========================================================

                
            existing_answer = (
                db.query(AttemptAnswer)
                .filter(
                    AttemptAnswer.attempt_id == attempt.id,
                    AttemptAnswer.question_id == payload.question_id,
                )
                .first()
            )

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

            previous_selected = (
                existing_answer.selected_option
                if existing_answer
                else ""
            )

            current_selected = selected_key or ""

            answer_changed = previous_selected != current_selected

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
        # UPSERT ANSWER (UNCHANGED LOGIC)
        # ==========================================================
        stmt = insert(AttemptAnswer).values(
            attempt_id=attempt.id,
            question_id=payload.question_id,
            selected_option=selected_key or "",
            is_correct=is_correct,
            hint_used=hint_used_final,
            hint_used_at=(
                now if (payload.hint_used and not hint_already_used)
                else (existing_answer.hint_used_at if existing_answer else None)
            ),
            answered_at=now,
            raw_score=raw_score,
            effective_score=effective_score,
            is_special=question["is_special"],
            weight_used=weight,
            first_hint_opened_at=(
                now
                if (
                    payload.hint_used
                    and (
                        not existing_answer
                        or existing_answer.first_hint_opened_at is None
                    )
                )
                else (
                    existing_answer.first_hint_opened_at
                    if existing_answer
                    else None
                )
            ),
            time_to_first_hint_seconds=(
                int((now - attempt.started_at).total_seconds())
                if (
                    payload.hint_used
                    and attempt.started_at
                    and (
                        not existing_answer
                        or existing_answer.time_to_first_hint_seconds is None
                    )
                )
                else (
                    existing_answer.time_to_first_hint_seconds
                    if existing_answer
                    else None
                )
            ),
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["attempt_id", "question_id"],
            set_={
                "selected_option": (
                    selected_key
                    if selected_key is not None
                    else (
                        existing_answer.selected_option
                        if existing_answer
                        else ""
                    )
                ),
                "is_correct": is_correct,
                "hint_used": hint_used_final,
                "answered_at": now,
                "raw_score": raw_score,
                "effective_score": effective_score,
                "hint_used_at": (
                    now if (payload.hint_used and not hint_already_used)
                    else (existing_answer.hint_used_at if existing_answer else None)
                ),
                "first_hint_opened_at": (
                    now
                    if (
                        payload.hint_used
                        and (
                            not existing_answer
                            or existing_answer.first_hint_opened_at is None
                        )
                    )
                    else (
                        existing_answer.first_hint_opened_at
                        if existing_answer
                        else None
                    )
                ),
                "time_to_first_hint_seconds": (
                    int((now - attempt.started_at).total_seconds())
                    if (
                        payload.hint_used
                        and attempt.started_at
                        and (
                            not existing_answer
                            or existing_answer.time_to_first_hint_seconds is None
                        )
                    )
                    else (
                        existing_answer.time_to_first_hint_seconds
                        if existing_answer
                        else None
                    )
                ),
            },
        )


        with trace.measure("answer_upsert"):
            db.execute(stmt)
        # ==========================================================
        # HINT COUNTER (UNCHANGED LOGIC)
        # ==========================================================
        if payload.hint_used and not hint_already_used:
            attempt.hints_used_count = (attempt.hints_used_count or 0) + 1

        # ==========================================================
        # CAPTURE BEFORE COMMIT
        # ==========================================================
        is_active = attempt.status == AttemptStatus.IN_PROGRESS
        total_hints_used = attempt.hints_used_count or 0

        with trace.measure("flush"):
            db.flush()

        with trace.measure("commit"):
            db.commit()


        # ==========================================================
        # EVENT LOGGING
        # ==========================================================
        with trace.measure("event_logging"):

            if is_active:

                try:

                    if answer_changed:
                        log_attempt_event(
                            db,
                            attempt.id,
                            payload.question_id,
                            EVENT_ANSWER_CHANGED,
                        )

                    if payload.hint_used and not hint_already_used:
                        log_attempt_event(
                            db,
                            attempt.id,
                            payload.question_id,
                            EVENT_HINT_USED,
                        )

                except Exception:
                    logger.exception("Failed to log attempt events")

            logger.info(
                "submit_answer_profile",
                extra={
                    "attempt_id": str(attempt.id),
                    **trace.summary(),
                },
            )

            logger.info(
                "request_trace",
                extra=trace.summary(),
            )

            return AnswerSubmitResponse(
                is_correct=is_correct,
                raw_score=float(raw_score),
                effective_score=float(effective_score),
                total_hints_used=total_hints_used,
            )

    except IntegrityError:
        db.rollback()
        conflict(ErrorCode.DATABASE_ERROR, "Answer submission conflict")

    except Exception:
        db.rollback()
        raise

    finally:
        trace.mark_endpoint_end()
    
    

# ==========================================================
# FINALIZE ATTEMPT
# ==========================================================

@router.post("/{attempt_id}/finalize")
def finalize_attempt_endpoint(
    request: Request,
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fully finalize an attempt.

    Manual submissions immediately execute the canonical
    finalization pipeline.
    """
    trace = RequestTrace(request)
    trace.mark_endpoint_start()

    try:
        attempt = (
            db.query(Attempt)
            .filter(
                Attempt.id == attempt_id,
                Attempt.participant.has(user_id=current_user.id),
            )
            .with_for_update()
            .first()
        )

        if attempt is None:
            not_found(
                ErrorCode.ATTEMPT_NOT_FOUND,
                "Attempt not found",
            )

        if attempt.status == AttemptStatus.SUBMITTED:
            return {
                "message": "Attempt already submitted"
            }

        if attempt.status != AttemptStatus.IN_PROGRESS:
            forbidden(
                ErrorCode.INVALID_ATTEMPT_STATE,
                "Attempt is not in progress",
            )

        finalize_attempt(db, attempt)

        db.commit()

        return {
            "message": "Submission accepted"
        }
    finally:
        trace.mark_endpoint_end()
# ==========================================================
# RESUME ATTEMPT
# ==========================================================
@router.get("/{attempt_id}/resume")
def resume_attempt(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.utils.seeded_order import build_attempt_order

    now = datetime.now(timezone.utc)

    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()

    if not attempt:
        not_found(ErrorCode.ATTEMPT_NOT_FOUND, "Attempt not found")

    if attempt.participant.user_id != current_user.id:
        forbidden(ErrorCode.FORBIDDEN, "Unauthorized attempt access")

    if attempt.status == AttemptStatus.SUBMITTED:
        forbidden(ErrorCode.ALREADY_COMPLETED, "Attempt already submitted")

    if attempt.status != AttemptStatus.IN_PROGRESS:
        forbidden(ErrorCode.ATTEMPT_NOT_ACTIVE, "Attempt is not active")

    actual_elapsed = int((now - attempt.started_at).total_seconds())

    # ==========================================================
    # Defensive timeout enforcement
    # ==========================================================
    if actual_elapsed >= attempt.allowed_duration_seconds:
        finalize_attempt(db, attempt)
        db.commit()

        forbidden(
            ErrorCode.ATTEMPT_EXPIRED,
            "Attempt time expired",
        )


    elapsed = min(
        actual_elapsed,
        attempt.allowed_duration_seconds
    )

    remaining = max(
        attempt.allowed_duration_seconds - elapsed,
        0
    )

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

    pool = attempt.question_pool_ids or {}

    base_ids = pool.get("base", [])
    bonus_ids = pool.get("bonus", [])

    navigation_order = build_attempt_order(
        base_ids=base_ids,
        bonus_ids=bonus_ids,
        seed=attempt.shuffle_seed,
        special_unlocked=attempt.special_unlocked,
    )

    return {
        "attempt_id": str(attempt.id),
        "status": attempt.status,
        "remaining_time_seconds": remaining,
        "special_unlocked": attempt.special_unlocked,
        "hints_used": attempt.hints_used_count,
        "progress": progress,
        "question_order": navigation_order,
    }


# ==========================================================
# HEARTBEAT
# ==========================================================
@router.post("/{attempt_id}/heartbeat")
def heartbeat_attempt(
    attempt_id: UUID,
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
        not_found(ErrorCode.ATTEMPT_NOT_FOUND, "Attempt not found")

    if attempt.participant.user_id != current_user.id:
        forbidden(ErrorCode.FORBIDDEN, "Unauthorized attempt access")

    if attempt.status != AttemptStatus.IN_PROGRESS:
        forbidden(ErrorCode.ATTEMPT_NOT_ACTIVE, "Attempt is not active")

    actual_elapsed = int((now - attempt.started_at).total_seconds())

    elapsed = min(
        actual_elapsed,
        attempt.allowed_duration_seconds
    )

    remaining = max(
        attempt.allowed_duration_seconds - elapsed,
        0
    )

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
    attempt_id: UUID,
    payload: QuestionViewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()

    if not attempt:
        not_found(ErrorCode.ATTEMPT_NOT_FOUND, "Attempt not found")

    if attempt.participant.user_id != current_user.id:
        forbidden(ErrorCode.FORBIDDEN, "Unauthorized")

    if attempt.status != AttemptStatus.IN_PROGRESS:
        return {"ok": True}

   # print("VIEW EVENT FIRED", attempt.id, payload.question_id)

    log_attempt_event(
        db,
        attempt_id=attempt.id,
        question_id=payload.question_id,
        event_type=EVENT_QUESTION_VIEWED,
    )

    db.commit()

    return {"ok": True}