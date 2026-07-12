from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import update, func

from app.models.attempt import Attempt, AttemptStatus
from app.models.attempt_answer import AttemptAnswer
from app.models.participant_progress import ParticipantProgress
from app.models.question import Question


def finalize_attempt(db: Session, attempt: Attempt):
    """
    Finalizes an exam attempt and updates participant progress atomically.
    """

    # ⭐ reload + LOCK attempt row
    attempt = (
        db.query(Attempt)
        .filter(Attempt.id == attempt.id)
        .with_for_update()
        .first()
    )

    if not attempt:
        return None

    # ✅ idempotency guard
    if attempt.progress_applied:
        return attempt

    now = datetime.now(timezone.utc)

    # ⏱ cap time at expiry if finalized late
    expiry_time = attempt.started_at + timedelta(
        seconds=attempt.allowed_duration_seconds
    )
    if now > expiry_time:
        now = expiry_time

    # ==========================================================
    # 2️⃣ Aggregate Scores (optimized — no N+1 queries)
    # ==========================================================
    answers = (
        db.query(
            AttemptAnswer.is_special,
            AttemptAnswer.raw_score,
            AttemptAnswer.effective_score,
        )
        .filter(AttemptAnswer.attempt_id == attempt.id)
        .all()
    )

    base_raw_total = Decimal("0")
    base_effective_total = Decimal("0")
    bonus_effective_total = Decimal("0")

    for answer in answers:
        if answer.is_special:
            bonus_effective_total += answer.effective_score
        else:
            base_raw_total += answer.raw_score
            base_effective_total += answer.effective_score

    final_score_total = base_effective_total + bonus_effective_total
    total_time = int((now - attempt.started_at).total_seconds())

    # ==========================================================
    # 3️⃣ Update Attempt State
    # ==========================================================
    attempt.raw_score = base_raw_total
    attempt.final_score = final_score_total
    attempt.total_time_seconds = max(total_time, 0)
    attempt.submitted_at = now
    attempt.status = AttemptStatus.SUBMITTED

    # ⭐ Golden Snapshot (immutable)
    if attempt.golden_snapshot is None:
        attempt.golden_snapshot = {
            "raw_score": str(attempt.raw_score),
            "final_score": str(attempt.final_score),
            "hints_used": attempt.hints_used_count,
            "special_unlocked": attempt.special_unlocked,
            "bonus_entered": attempt.bonus_entered,
            "total_time_seconds": attempt.total_time_seconds,
            "submitted_at": attempt.submitted_at.isoformat(),
            "scoring_version": attempt.scoring_version,
        }

    # ==========================================================
    # 4️⃣ Atomic Progress Update
    # ==========================================================
    progress = (
        db.query(ParticipantProgress)
        .filter(
            ParticipantProgress.challenge_id == attempt.challenge_id,
            ParticipantProgress.participant_id == attempt.participant_id,
        )
    #   .with_for_update(nowait=True)
        .with_for_update(skip_locked=True)
        .first()
    )

    if not progress:
        progress = ParticipantProgress(
            challenge_id=attempt.challenge_id,
            participant_id=attempt.participant_id,
            cumulative_score=Decimal("0"),
            cumulative_base_effective_score=Decimal("0"),
            cumulative_base_max=Decimal("0"),
            days_completed=0,
            attendance_count=0,
        )
        db.add(progress)
        db.flush()

    # ==========================================================
    # 🔥 OPTIMIZED: base max calculation (CRITICAL FIX)
    # ==========================================================
    base_max_today = (
        db.query(func.coalesce(func.sum(Question.weight), 0))
        .filter(
            Question.exam_day_id == attempt.exam_day_id,
            Question.is_special == False,
        )
        .scalar()
    )

    base_max_today = Decimal(base_max_today)

    # ==========================================================
    # eligibility logic
    # ==========================================================
    new_days_completed = progress.days_completed + 1
    new_attendance = progress.attendance_count + 1
    new_cumulative_base_eff = (
        progress.cumulative_base_effective_score + base_effective_total
    )
    new_cumulative_base_max = progress.cumulative_base_max + base_max_today

    eligible_next = False
    if new_cumulative_base_max > 0 and new_days_completed >= 2:
        pct = (new_cumulative_base_eff / new_cumulative_base_max) * Decimal("100")
        eligible_next = (
            pct >= Decimal("70") and new_attendance == new_days_completed
        )

    # ==========================================================
    # atomic increment
    # ==========================================================
    stmt = (
        update(ParticipantProgress)
        .where(ParticipantProgress.id == progress.id)
        .values(
            cumulative_score=ParticipantProgress.cumulative_score + final_score_total,
            cumulative_base_effective_score=ParticipantProgress.cumulative_base_effective_score + base_effective_total,
            cumulative_base_max=ParticipantProgress.cumulative_base_max + base_max_today,
            days_completed=ParticipantProgress.days_completed + 1,
            attendance_count=ParticipantProgress.attendance_count + 1,
            eligible_for_bonus_next_day=eligible_next,
            last_updated=now,
        )
    )
    db.execute(stmt)

    db.flush()

    # ✅ idempotency completion marker
    attempt.progress_applied = True

    return attempt