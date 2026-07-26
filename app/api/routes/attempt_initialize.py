import uuid
import logging

from datetime import datetime, timezone, timedelta
from time import perf_counter

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.api.deps import get_db, get_current_user
from app.models.attempt import Attempt, AttemptStatus
from app.models.challenge import ChallengeStatus
from app.models.participant import AccountStatus
from app.models.user import User
from app.schemas.attempt import (
    AttemptStartRequest,
    AttemptStartResponse,
)
from app.services.question_cache import (
    get_exam_day_questions_cached,
)

from app.services.attempt_repository import (
    AttemptRepository,
)
from app.core.errors import forbidden
from app.core.error_codes import ErrorCode
from app.core.request_trace import RequestTrace
from app.core.request_context import (
    get_request_id,
    elapsed_ms,
)

router = APIRouter(tags=["Attempt Initialization"])

logger = logging.getLogger(__name__)

grace_seconds = 30

@router.post("/initialize", response_model=AttemptStartResponse)
def initialize_attempt(
    request: Request,
    payload: AttemptStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    trace = RequestTrace(request)
    trace.mark_endpoint_start()

    logger.info(
        "INITIALIZE_ATTEMPT_ENTER",
        extra={
            "request_id": get_request_id(),
            "elapsed_ms": elapsed_ms(),
        },
    )

    request_start = perf_counter()
    connection_wait_start = None
    try:
        connection_wait_start = perf_counter()

        with trace.measure("start_context_lookup"):
            ctx = AttemptRepository.get_start_attempt_context(
                db=db,
                exam_day_id=payload.exam_day_id,
                user_id=current_user.id,
            )

        connection_wait_ms = round(
            (perf_counter() - connection_wait_start) * 1000,
            2,
        )

        logger.info(
            "first_query_completed",
            extra={
                "request_id": get_request_id(),
                "elapsed_ms": elapsed_ms(),
                "connection_wait_ms": connection_wait_ms,
                "pool_status": db.bind.pool.status(),
            },
        )

        if ctx is None:
            forbidden(
                ErrorCode.FORBIDDEN,
                "User not enrolled for this challenge",
            )

        if ctx.challenge_status != ChallengeStatus.ACTIVE:
            forbidden(
                ErrorCode.FORBIDDEN,
                "Challenge not active",
            )

        if ctx.account_status != AccountStatus.ACTIVE:
            forbidden(
                ErrorCode.FORBIDDEN,
                "Participant account not active",
            )

        now = datetime.now(timezone.utc)

        if (
            now < ctx.window_start - timedelta(seconds=grace_seconds)
            or now > ctx.window_end + timedelta(seconds=grace_seconds)
        ):
            forbidden(
                ErrorCode.WINDOW_CLOSED,
                "Exam window not active",
            )

        if ctx.is_force_locked:
            forbidden(
                ErrorCode.FORCE_LOCKED,
                "Exam is force locked",
            )

        special_unlocked = (
            ctx.days_completed >= 2
            and ctx.eligible_for_bonus_next_day
        )
        with trace.measure("question_cache"):
            questions_map = get_exam_day_questions_cached(str(ctx.exam_day_id))

        questions = list(questions_map.values())

        base_ids = sorted(
            [q["id"] for q in questions if not q["is_special"]]
        )

        bonus_ids = sorted(
            [q["id"] for q in questions if q["is_special"]]
        )
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

        stmt = insert(Attempt).values(
            id=uuid.uuid4(),
            challenge_id=ctx.challenge_id,
            participant_id=ctx.participant_id,
            exam_day_id=ctx.exam_day_id,

            status=AttemptStatus.NOT_STARTED,

            special_unlocked=special_unlocked,

            started_at=None,

            allowed_duration_seconds=total_allowed,

            hints_used_count=0,

            attendance_flag=False,

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
    
#            with trace.measure("flush"):
#                db.flush()

            with trace.measure("commit"):
                db.commit()

            logger.info(
                "INITIALIZE_COMMIT_DONE",
                extra={
                    "request_id": get_request_id(),
                    "elapsed_ms": elapsed_ms(),
                },
            )

            


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
                "initialize_attempt_profile",
                extra={
                    "participant_id": str(ctx.participant_id),
                    "attempt_created": True,
                    "total_ms": total_ms,
                    "connection_wait_ms": connection_wait_ms,
                    "pool_status": db.bind.pool.status(),
                    "trace": trace.summary(),
                },
            )

            return response

        # ==========================================================
        # ✅ CASE 2: EXISTING ATTEMPT (FALLBACK)
        # ==========================================================
        with trace.measure("existing_attempt_lookup"):
            attempt = (
                db.query(Attempt)
                .filter(
                    Attempt.participant_id == ctx.participant_id,
                    Attempt.exam_day_id == ctx.exam_day_id,
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
            "initialize_attempt_profile",
            extra={
                "participant_id": str(ctx.participant_id),
                "attempt_created": False,
                "total_ms": total_ms,
                "connection_wait_ms": connection_wait_ms,
                "pool_status": db.bind.pool.status(),
                "trace": trace.summary(),
            },
        )

        return response
    except Exception:
        if db.is_active:
            db.rollback()
        raise

    finally:
        logger.info(
            "INITIALIZE_ATTEMPT_FINALLY",
            extra={
                "request_id": get_request_id(),
                "elapsed_ms": elapsed_ms(),
            },
        )

        trace.mark_endpoint_end()

        logger.info(
            "INITIALIZE_ATTEMPT_EXIT",
            extra={
                "request_id": get_request_id(),
                "elapsed_ms": elapsed_ms(),
            },
        )
        

