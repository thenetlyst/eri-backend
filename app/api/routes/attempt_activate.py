import logging

from datetime import datetime, timezone
from time import perf_counter

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user

from app.models.attempt import Attempt, AttemptStatus
from app.models.user import User

from app.schemas.attempt import (
    AttemptStartRequest,
    AttemptStartResponse,
)

from app.core.errors import (
    forbidden,
    not_found,
)

from app.core.error_codes import ErrorCode
from app.core.request_trace import RequestTrace
from app.core.request_context import get_request_id

router = APIRouter(tags=["Attempt Activation"])

logger = logging.getLogger(__name__)

# ==========================================================
# ACTIVATE ATTEMPT
# ==========================================================
@router.post("/activate", response_model=AttemptStartResponse)
def activate_attempt(
    request: Request,
    payload: AttemptStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trace = RequestTrace(request)
    trace.mark_endpoint_start()

    logger.info(
        "ACTIVATE_ATTEMPT_ENTER",
        extra={
            "request_id": get_request_id(),
        },
    )

    request_start = perf_counter()

    try:
        now = datetime.now(timezone.utc)

        with trace.measure("attempt_lock"):
            attempt = (
                db.query(Attempt)
                .filter(
                    Attempt.exam_day_id == payload.exam_day_id,
                    Attempt.participant.has(user_id=current_user.id),
                )
                .with_for_update()
                .first()
            )

        # ------------------------------------------------------
        # Attempt not found
        # ------------------------------------------------------
        if attempt is None:
            not_found(
                ErrorCode.ATTEMPT_NOT_FOUND,
                "Attempt not found",
            )

        # ------------------------------------------------------
        # Already submitted
        # ------------------------------------------------------
        if attempt.status == AttemptStatus.SUBMITTED:
            forbidden(
                ErrorCode.ALREADY_COMPLETED,
                "Attempt already submitted",
                meta={"attempt_id": str(attempt.id)},
            )

        # ------------------------------------------------------
        # Idempotent activation
        # ------------------------------------------------------
        if attempt.status == AttemptStatus.IN_PROGRESS:

            logger.info(
                "activate_attempt_profile",
                extra={
                    "participant_id": str(attempt.participant_id),
                    "already_active": True,
                    "total_ms": round(
                        (perf_counter() - request_start) * 1000,
                        2,
                    ),
                    "trace": trace.summary(),
                },
            )

            return AttemptStartResponse(
                attempt_id=attempt.id,
                allowed_duration_seconds=attempt.allowed_duration_seconds,
                special_unlocked=attempt.special_unlocked,
            )

        # ------------------------------------------------------
        # Defensive lifecycle validation
        # ------------------------------------------------------
        if attempt.status != AttemptStatus.NOT_STARTED:
            forbidden(
                ErrorCode.INVALID_ATTEMPT_STATE,
                "Attempt cannot be activated",
            )

        if attempt.started_at is not None:
            forbidden(
                ErrorCode.INVALID_ATTEMPT_STATE,
                "Attempt already initialized",
            )

        # ------------------------------------------------------
        # Activate
        # ------------------------------------------------------
        attempt.status = AttemptStatus.IN_PROGRESS
        attempt.started_at = now
        attempt.attendance_flag = True

        with trace.measure("db_write"):

            with trace.measure("flush"):
                db.flush()

            with trace.measure("commit"):
                db.commit()

        logger.info(
            "activate_attempt_profile",
            extra={
                "participant_id": str(attempt.participant_id),
                "already_active": False,
                "total_ms": round(
                    (perf_counter() - request_start) * 1000,
                    2,
                ),
                "trace": trace.summary(),
            },
        )

        return AttemptStartResponse(
            attempt_id=attempt.id,
            allowed_duration_seconds=attempt.allowed_duration_seconds,
            special_unlocked=attempt.special_unlocked,
        )

    except Exception:
        if db.is_active:
            db.rollback()
        raise

    finally:
        trace.mark_endpoint_end()

        logger.info(
            "ACTIVATE_ATTEMPT_EXIT",
            extra={
                "request_id": get_request_id(),
            },
        )