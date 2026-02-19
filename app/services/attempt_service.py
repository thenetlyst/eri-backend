from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.attempt import Attempt, AttemptStatus
from app.models.attempt_answer import AttemptAnswer
from app.models.question import Question
from app.models.participant_progress import ParticipantProgress


def finalize_attempt(db: Session, attempt: Attempt):
    """
    Finalizes an attempt using Absolute Additive Scoring (Season 1 model).

    - Leaderboard uses additive final score
    - Bonus eligibility uses BASE performance only
    - Fully idempotent
    """

    # -------------------------------------------------
    # 1️⃣ Prevent Double Finalization (Idempotent)
    # -------------------------------------------------
    if attempt.status == AttemptStatus.SUBMITTED:
        return attempt

    now = datetime.now(timezone.utc)

    expiry_time = attempt.started_at + timedelta(
        seconds=attempt.allowed_duration_seconds
    )

    if now > expiry_time:
        now = expiry_time

    # -------------------------------------------------
    # 2️⃣ Fetch All Answers
    # -------------------------------------------------
    answers = (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt.id)
        .all()
    )

    # -------------------------------------------------
    # 3️⃣ Separate Base and Bonus Scores
    # -------------------------------------------------
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

    # -------------------------------------------------
    # 4️⃣ Final Additive Score
    # -------------------------------------------------
    raw_score_total = base_raw_total
    final_score_total = base_effective_total + bonus_effective_total

    total_time = int((now - attempt.started_at).total_seconds())

    # -------------------------------------------------
    # 5️⃣ Update Attempt Row
    # -------------------------------------------------
    attempt.raw_score = raw_score_total
    attempt.final_score = final_score_total
    attempt.total_time_seconds = total_time
    attempt.submitted_at = now
    attempt.status = AttemptStatus.SUBMITTED

    # -------------------------------------------------
    # 6️⃣ Update Participant Progress (LOCKED)
    # -------------------------------------------------
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

    # -------------------------------------------------
    # 7️⃣ Update Leaderboard Total
    # -------------------------------------------------
    progress.cumulative_score += final_score_total

    # -------------------------------------------------
    # 8️⃣ Compute Base Max For Today (No Bonus)
    # -------------------------------------------------
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

    # Update BASE tracking (for eligibility math)
    progress.cumulative_base_effective_score += base_effective_total
    progress.cumulative_base_max += base_max_today

    progress.days_completed += 1
    progress.attendance_count += 1

    # -------------------------------------------------
    # 9️⃣ Bonus Eligibility Logic (Base Only)
    # -------------------------------------------------
    if (
        progress.days_completed >= 2
        and progress.cumulative_base_max > 0
    ):

        base_percentage = (
            progress.cumulative_base_effective_score
            / progress.cumulative_base_max
        ) * Decimal("100")

        progress.eligible_for_bonus_next_day = (
            base_percentage >= Decimal("70")
            and progress.attendance_count == progress.days_completed
        )
    else:
        progress.eligible_for_bonus_next_day = False

    progress.last_updated = datetime.now(timezone.utc)

    return attempt
