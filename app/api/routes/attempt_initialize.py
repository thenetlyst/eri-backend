import uuid

from datetime import datetime, timezone, timedelta
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


router = APIRouter(tags=["Attempt Initialization"])

grace_seconds = 30

@router.post("/initialize", response_model=AttemptStartResponse)
def initialize_attempt(
    request: Request,
    payload: AttemptStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        ctx = AttemptRepository.get_start_attempt_context(
            db=db,
            exam_day_id=payload.exam_day_id,
            user_id=current_user.id,
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
        questions_map = get_exam_day_questions_cached(str(ctx.exam_day_id))

        questions = list(questions_map.values())

        base_ids = sorted(
            [q["id"] for q in questions if not q["is_special"]]
        )

        bonus_ids = sorted(
            [q["id"] for q in questions if q["is_special"]]
        )
        if not base_ids:

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

        result = db.execute(stmt)
        row = result.fetchone()
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
            response = AttemptStartResponse(
                attempt_id=row.id,
                allowed_duration_seconds=row.allowed_duration_seconds,
                special_unlocked=row.special_unlocked,
            )
            return response

        # ==========================================================
        # ✅ CASE 2: EXISTING ATTEMPT (FALLBACK)
        # ==========================================================
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

        response = AttemptStartResponse(
            attempt_id=attempt.id,
            allowed_duration_seconds=attempt.allowed_duration_seconds,
            special_unlocked=attempt.special_unlocked,
        )


        return response
    except Exception:
        if db.is_active:
            db.rollback()
        raise

        

