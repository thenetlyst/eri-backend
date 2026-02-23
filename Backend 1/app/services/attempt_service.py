from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.attempt import Attempt, AttemptStatus
from app.models.attempt_answer import AttemptAnswer
from app.models.question import Question
from app.models.participant_progress import ParticipantProgress


def finalize_attempt(db: Session, attempt: Attempt):
    """
    FINAL — Idempotent per exam_day
    Safe for manual + worker finalize
    """

    now = datetime.now(timezone.utc)

    # -------------------------------------------
    # 1️⃣ Compute expiry safe
    # -------------------------------------------
    expiry_time = attempt.started_at + timedelta(
        seconds=attempt.allowed_duration_seconds
    )

    if now > expiry_time:
        now = expiry_time

    # -------------------------------------------
    # 2️⃣ Fetch answers
    # -------------------------------------------
    answers = (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt.id)
        .all()
    )

    base_raw_total = Decimal("0")
    base_effective_total = Decimal("0")
    bonus_effective_total = Decimal("0")

    for answer in answers:
        question = (
            db.query(Question)
            .filter(Question.id == answer.question_id)
            .first()
        )

        if not question:
            continue

        if question.is_special:
            bonus_effective_total += answer.effective_score
        else:
            base_raw_total += answer.raw_score
            base_effective_total += answer.effective_score

    raw_score_total = base_raw_total
    final_score_total = base_effective_total + bonus_effective_total
    total_time = int((now - attempt.started_at).total_seconds())

    # -------------------------------------------
    # 3️⃣ Update attempt (always allowed)
    # -------------------------------------------
    attempt.raw_score = raw_score_total
    attempt.final_score = final_score_total
    attempt.total_time_seconds = total_time
    attempt.submitted_at = now
    attempt.status = AttemptStatus.SUBMITTED

    # -------------------------------------------
    # 4️⃣ Lock progress row
    # -------------------------------------------
    progress = (
        db.query(ParticipantProgress)
        .filter(
            ParticipantProgress.challenge_id == attempt.challenge_id,
            ParticipantProgress.participant_id == attempt.participant_id,
        )
        .with_for_update()
        .first()
    )

    if not progress:
        progress = ParticipantProgress(
            challenge_id=attempt.challenge_id,
            participant_id=attempt.participant_id,
        )
        db.add(progress)
        db.flush()

    # -------------------------------------------
    # ⭐ 5️⃣ TRUE IDEMPOTENCY — per exam_day
    # -------------------------------------------
    existing_attempt_for_day = (
        db.query(Attempt)
        .filter(
            Attempt.participant_id == attempt.participant_id,
            Attempt.exam_day_id == attempt.exam_day_id,
            Attempt.status == AttemptStatus.SUBMITTED,
            Attempt.id != attempt.id,
        )
        .first()
    )

    if existing_attempt_for_day:
        # Progress already counted earlier
        progress.last_updated = now
        return attempt

    # -------------------------------------------
    # 6️⃣ Leaderboard total
    # -------------------------------------------
    progress.cumulative_score += final_score_total

    # -------------------------------------------
    # 7️⃣ Base max today
    # -------------------------------------------
    base_questions = (
        db.query(Question)
        .filter(
            Question.exam_day_id == attempt.exam_day_id,
            Question.is_special == False,
        )
        .all()
    )

    base_max_today = sum(
        (Decimal(q.weight) for q in base_questions),
        Decimal("0"),
    )

    progress.cumulative_base_effective_score += base_effective_total
    progress.cumulative_base_max += base_max_today

    progress.days_completed += 1
    progress.attendance_count += 1

    # -------------------------------------------
    # 8️⃣ Bonus eligibility
    # -------------------------------------------
    if progress.cumulative_base_max > 0 and progress.days_completed >= 2:
        pct = (
            progress.cumulative_base_effective_score
            / progress.cumulative_base_max
        ) * Decimal("100")

        progress.eligible_for_bonus_next_day = (
            pct >= Decimal("70")
            and progress.attendance_count == progress.days_completed
        )
    else:
        progress.eligible_for_bonus_next_day = False

    progress.last_updated = now

    return attempt